import unittest
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.failure_worlds import REQUIRED as WORLDS
class TestGlobalCorrespondence(unittest.TestCase):
    def test_methods_engines_tls_worlds_reactor(self):
        require_methodologies(REQUIRED_METHODOLOGIES)
        sig=("a"*64,"b"*64,"c"*64)
        require_engine_correspondence([EngineWitness("BEAM","beam","otp",*sig),EngineWitness("WASM","wasmtime","component",*sig)])
        require_multi_region_tls([RegionWitness("h1","us",True,"d"*64,4),RegionWitness("h2","eu",True,"e"*64,4)],4)
        require_failure_worlds(WORLDS)
        s=Subject("o/r","3"*40,"x")
        require_reactor_chain([Stage(n,s,str(i)*64) for i,n in enumerate(("semantic","reactor","certificate","federation","realization","receipt"),1)],s)
