#!/usr/bin/env python
"""
    WorkQueue tests
"""

import tempfile
import unittest
import cProfile
import pstats
import shutil

from WMCore.Services.EmulatorSwitch import EmulatorHelper
from WMQuality.Emulators.DataBlockGenerator import Globals
from WMQuality.Emulators.DataBlockGenerator.Globals import GlobalParams
from WMQuality.Emulators.WMSpecGenerator.WMSpecGenerator import WMSpecGenerator
from WMCore.WorkQueue.WorkQueue import WorkQueue, globalQueue, localQueue
from WorkQueueTestCase import WorkQueueTestCase


class LocalWorkQueueProfileTest(WorkQueueTestCase):
    """
    _WorkQueueTest_
    
    """
    
    def setUp(self):
        """
        If we dont have a wmspec file create one
        """

        EmulatorHelper.setEmulators(phedex = True, dbs = True, 
                                    siteDB = True, requestMgr = True)
        WorkQueueTestCase.setUp(self)
        
        self.specGenerator = WMSpecGenerator()
        self.specs = self.createReRecoSpec(1, "file")
        
        self.cacheDir = tempfile.mkdtemp() 
 
        # Create queues
        self.localQueue = localQueue(CacheDir = self.cacheDir,
                                     NegotiationTimeout = 0,
                                     QueueURL = 'global.example.com')
        
        
    def tearDown(self):
        """tearDown"""
        WorkQueueTestCase.tearDown(self)
        try:
            shutil.rmtree( self.cacheDir )
            self.specGenerator.removeSpecs()
        except:
            pass
        EmulatorHelper.resetEmulators()
        
    def createReRecoSpec(self, numOfSpec, type = "spec"):
        specs = []    
        for i in range(numOfSpec):
            specName = "MinBiasProcessingSpec_Test_%s" % (i+1)
            specs.append(self.specGenerator.createReRecoSpec(specName, type))
        return specs
    
    def createProfile(self, name, function):
        file = name
        prof = cProfile.Profile()
        prof.runcall(function)
        prof.dump_stats(file)
        p = pstats.Stats(file)
        p.strip_dirs().sort_stats('cumulative').print_stats(0.1)
        p.strip_dirs().sort_stats('time').print_stats(0.1)
        p.strip_dirs().sort_stats('calls').print_stats(0.1)
        #p.strip_dirs().sort_stats('name').print_stats(10)
            
    def testGetWorkLocalQueue(self):

        for spec in self.specs:
            self.localQueue.queueWork(spec, team = "A-team")
        self.localQueue.updateLocationInfo()
        self.createProfile('getWorkProfile.prof',
                           self.localQueueGetWork)
        
    def localQueueGetWork(self):
        siteJobs = {}
        for site in Globals.SITES:
            siteJobs[site] = 100000
        self.localQueue.getWork(siteJobs, team = "A-team")
                             
        
if __name__ == "__main__":
    unittest.main()