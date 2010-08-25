#!/usr/bin/env python
"""
_JobGroup_t_

Unit tests for the WMBS JobGroup class.
"""

__revision__ = "$Id: JobGroup_t.py,v 1.16 2009/03/18 20:03:01 sfoulkes Exp $"
__version__ = "$Revision: 1.16 $"

import unittest
import logging
import os
import commands
import threading
import random
from sets import Set

from WMCore.Database.DBCore import DBInterface
from WMCore.Database.DBFactory import DBFactory
from WMCore.DataStructs.Fileset import Fileset
from WMCore.DAOFactory import DAOFactory
from WMCore.WMBS.File import File
from WMCore.WMBS.Fileset import Fileset as WMBSFileset
from WMCore.WMBS.Job import Job
from WMCore.WMBS.JobGroup import JobGroup
from WMCore.WMBS.Workflow import Workflow
from WMCore.WMBS.Subscription import Subscription
from WMCore.WMFactory import WMFactory
from WMQuality.TestInit import TestInit
from WMCore.DataStructs.Run import Run

class JobGroupTest(unittest.TestCase):
    _setup = False
    _teardown = False

    def runTest(self):
        """
        _runTest_

        Run all the unit tests.
        """
        unittest.main()
    
    def setUp(self):
        """
        _setUp_

        Setup the database and logging connection.  Try to create all of the
        WMBS tables.
        """
        if self._setup:
            return

        self.testInit = TestInit(__file__, os.getenv("DIALECT"))
        self.testInit.setLogging()
        self.testInit.setDatabaseConnection()
        self.testInit.setSchema(customModules = ["WMCore.WMBS"],
                                useDefault = False)
        
        self._setup = True
        return
               
    def tearDown(self):        
        """
        _tearDown_
        
        Drop all the WMBS tables.
        """
        myThread = threading.currentThread()
        
        if self._teardown:
            return
        
        factory = WMFactory("WMBS", "WMCore.WMBS")
        destroy = factory.loadObject(myThread.dialect + ".Destroy")
        myThread.transaction.begin()
        destroyworked = destroy.execute(conn = myThread.transaction.conn)
        if not destroyworked:
            raise Exception("Could not complete WMBS tear down.")
        myThread.transaction.commit()
            
        self._teardown = True
    
    def createTestJobGroupA(self, commitFlag = True):
        """
        _createTestJobGroupA_
        
               with testSubscription 
                     using testWorkflow (wf001) and testWMBSFilset
        add testJobA with testFileA and testJobB with testFileB
            to testJobGroupA
        return testJobGroupA
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testWMBSFileset = WMBSFileset(name = "TestFileset")
        testWMBSFileset.create()
        
        testSubscription = Subscription(fileset = testWMBSFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroupA = JobGroup(subscription = testSubscription)
        testJobGroupA.create()

        testFileA = File(lfn = "/this/is/a/lfnA", size = 1024, events = 10)
        testFileA.addRun(Run(10, *[12312]))

        testFileB = File(lfn = "/this/is/a/lfnB", size = 1024, events = 10)
        testFileB.addRun(Run(10, *[12312]))
        testFileA.create()
        testFileB.create()

        testJobA = Job(name = "TestJobA")
        testJobA.addFile(testFileA)
        
        testJobB = Job(name = "TestJobB")
        testJobB.addFile(testFileB)
        
        testJobGroupA.add(testJobA)
        testJobGroupA.add(testJobB)
        if commitFlag:
            testJobGroupA.commit()
        
        return testJobGroupA
    
    def testCreateDeleteExists(self):
        """
        _testCreateDeleteExists_

        Create a JobGroup and then delete it.  Use the JobGroup's exists()
        method to determine if it exists before it is created, after it is
        created and after it is deleted.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"
        
        testJobGroup.delete()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after it was deleted"

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return

    def testCreateTransaction(self):
        """
        _testCreateTransaction_

        Create a JobGroup and commit it to the database.  Rollback the database
        transaction and verify that the JobGroup is no longer in the database.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"
        
        myThread.transaction.rollback()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after transaction was rolled back."

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return    

    def testDeleteTransaction(self):
        """
        _testDeleteTransaction_

        Create a JobGroup and then commit it to the database.  Begin a
        transaction and the delete the JobGroup from the database.  Using the
        exists() method verify that the JobGroup is not in the database.
        Finally, roll back the transaction and verify that the JobGroup is
        in the database.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testJobGroup.delete()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after it was deleted"

        myThread.transaction.rollback()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after transaction was rolled back."        

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return

    def testLoad(self):
        """
        _testLoad_

        Test loading the JobGroup and any associated meta data from the
        database.
        """
        testJobGroupA = self.createTestJobGroupA()
        
        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.load()
        testJobGroupC = JobGroup(uid = testJobGroupA.uid)
        testJobGroupC.load()

        assert type(testJobGroupB.id) == int, \
               "ERROR: Job group id is not an int."

        assert type(testJobGroupC.id) == int, \
               "ERROR: Job group id is not an int."        

        assert type(testJobGroupB.subscription["id"]) == int, \
               "ERROR: Job group subscription id is not an int."

        assert type(testJobGroupC.subscription["id"]) == int, \
               "ERROR: Job group subscription id is not an int."        

        assert type(testJobGroupB.groupoutput.id) == int, \
               "ERROR: Job group output id is not an int."

        assert type(testJobGroupC.groupoutput.id) == int, \
               "ERROR: Job group output id is not an int."        

        assert testJobGroupB.uid == testJobGroupA.uid, \
               "ERROR: Job group did not load uid correctly."

        assert testJobGroupC.id == testJobGroupA.id, \
               "ERROR: Job group did not load id correctly."
        
        assert testJobGroupB.subscription["id"] == \
               testJobGroupA.subscription["id"], \
               "ERROR: Job group did not load subscription correctly"

        assert testJobGroupC.subscription["id"] == \
               testJobGroupA.subscription["id"], \
               "ERROR: Job group did not load subscription correctly"        

        assert testJobGroupB.groupoutput.id == testJobGroupA.groupoutput.id, \
               "ERROR: Output fileset didn't load properly"

        assert testJobGroupC.groupoutput.id == testJobGroupA.groupoutput.id, \
               "ERROR: Output fileset didn't load properly"        
        
        return

    def testLoadData(self):
        """
        _testLoadData_

        Test loading the JobGroup, it's meta data and any data associated with
        its output fileset and jobs from the database.
        """
        testJobGroupA = self.createTestJobGroupA()

        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.loadData()

        assert testJobGroupB.subscription["id"] == \
               testJobGroupA.subscription["id"], \
               "ERROR: Job group did not load subscription correctly"

        goldenJobs = testJobGroupA.getJobIDs(type="list")
        for job in testJobGroupB.jobs:
            assert job.id in goldenJobs, \
                   "ERROR: JobGroup loaded an unknown job"
            goldenJobs.remove(job.id)

        assert len(goldenJobs) == 0, \
            "ERROR: JobGroup didn't load all jobs"

        assert testJobGroupB.groupoutput.id == testJobGroupA.groupoutput.id, \
               "ERROR: Output fileset didn't load properly"
        
        return    

    def testCommit(self):
        """
        _testCommit_

        Verify that jobs are not added to a job group until commit() is called
        on the JobGroup.  Also verify that commit() correctly commits the jobs
        to the database.
        """
        testJobGroupA = self.createTestJobGroupA(commitFlag = False)

        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.loadData()

        assert len(testJobGroupA.jobs) == 0, \
               "ERROR: Original object commited too early"

        assert len(testJobGroupB.jobs) == 0, \
               "ERROR: Loaded JobGroup has too many jobs"

        testJobGroupA.commit()

        assert len(testJobGroupA.jobs) == 2, \
               "ERROR: Original object did not commit jobs"

        testJobGroupC = JobGroup(id = testJobGroupA.id)
        testJobGroupC.loadData()

        assert len(testJobGroupC.jobs) == 2, \
               "ERROR: Loaded object has too few jobs."

    def testCommitTransaction(self):
        """
        _testCommitTransaction_

        Create a JobGroup and then add some jobs to it.  Begin a transaction
        and then call commit() on the JobGroup.  Verify that the newly committed
        jobs can be loaded from the database.  Rollback the transaction and then
        verify that the jobs that were committed before are no longer associated
        with the JobGroup.
        """
        testJobGroupA = self.createTestJobGroupA(commitFlag = False)
        
        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.loadData()

        assert len(testJobGroupA.jobs) == 0, \
               "ERROR: Original object commited too early"

        assert len(testJobGroupB.jobs) == 0, \
               "ERROR: Loaded JobGroup has too many jobs"

        myThread = threading.currentThread()
        myThread.transaction.begin()

        testJobGroupA.commit()

        assert len(testJobGroupA.jobs) == 2, \
               "ERROR: Original object did not commit jobs"

        testJobGroupC = JobGroup(id = testJobGroupA.id)
        testJobGroupC.loadData()

        assert len(testJobGroupC.jobs) == 2, \
               "ERROR: Loaded object has too few jobs."        

        myThread.transaction.rollback()

        testJobGroupD = JobGroup(id = testJobGroupA.id)
        testJobGroupD.loadData()

        assert len(testJobGroupD.jobs) == 0, \
               "ERROR: Loaded object has too many jobs."        

        return

    def testRecordSubscriptionStatus(self):
        """
        _testRecordSubscriptionStatus_

        Create a JobGroup and then add some jobs to it. commit the job group
        and change the status of input file status of the jobs        
        """
        testJobGroupA = self.createTestJobGroupA()
        
        jobs = testJobGroupA.getJobIDs(type = "JobList")
        
        assert testJobGroupA.status() == "ACTIVE", \
               """ Error: All the jobs in available state: 
                   JobGroup should be in ACTIVE State """
                    
        for job in jobs:
            job.load()
        
        jobs[0].changeStatus("ACTIVE")
        
        assert testJobGroupA.status() == "ACTIVE", \
               """ Error:  One job is in active state: 
                   JobGroup should be in ACTIVE State """
        
        jobs[1].changeStatus("ACTIVE")
        
        assert testJobGroupA.status() == "ACTIVE", \
               """ Error:  All jobs is in active state: 
                   JobGroup should be in ACTIVE State """
                   
        jobs[0].changeStatus("COMPLETE")
        
        assert testJobGroupA.status() == "ACTIVE", \
               """ Error:  One job is in active state: 
                   JobGroup should be in ACTIVE State """
        
        jobs[1].changeStatus("COMPLETE")
        
        assert testJobGroupA.status() == "COMPLETE", \
               """ Error:  both jobs are in COMPLETE state: 
                   JobGroup should be in COMPLETE State """
                
        jobs[1].changeStatus("FAILED")
        
        assert testJobGroupA.status() == "FAILED", \
               """ Error:  one job is in FAILED state: 
                   JobGroup should be in FAILD State: %s"""
        
        # these will always return true according if no error occurs.
        # To do: check actual files state 
        assert testJobGroupA.recordAcquire() == True, \
                "Error : recordAcquier failed"
        assert testJobGroupA.recordComplete() == True, \
                "Error : recordComplete failed"
        assert testJobGroupA.recordFail() == True, \
                "Error : recordFail failed"
                
    def testOutput(self):
        """
        _testOutput_ 

        test adding output files in job group
        """
        testJobGroupA = self.createTestJobGroupA()
        
        jobs = testJobGroupA.getJobIDs(type = "JobList")
        count = 0 
        lfnSet = Set()           
        for job in jobs:
            job.load()
            count += 1
            fileName = "/this/is/a/lfnOut%s" % count
            lfnSet.add(fileName)
            testFile = File(lfn = fileName, size = 1024, events = 10)
            testFile.create()
            job.addOutput(testFile)
            testJobGroupA.addOutput(testFile)
        
        outputFileset = testJobGroupA.output()    
        assert outputFileset == False, \
               "Error: JobGroup is not completed but returns value %s"\
               % outputFileset
                  
        for job in jobs:
            job.changeStatus("COMPLETE")
        
        outputFileset = testJobGroupA.output() 
        outputFileset.loadData()
        
        outputLfns = Set()
        for file in outputFileset.files:
            outputLfns.add(file['lfn'])
        
        assert (lfnSet - outputLfns) == Set(), \
               "Error: output files doesn't match %s" % outputLfns
                  
if __name__ == "__main__":
    unittest.main() 
