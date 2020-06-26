from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
import mininet.clean
from mock import patch
import time
import os
import signal

class RingTopo( Topo ):
    "Ring topology with three switches and one host connected to each switch"

    def build( self ):
        # Create two hosts.
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )

        # Create the switches
        s1 = self.addSwitch( 's1' )
        s2 = self.addSwitch( 's2' )
        s3 = self.addSwitch( 's3' )

        # Add links between the switch and each host
        self.addLink( s1, h1 )
        self.addLink( s2, h2 )
        self.addLink( s3, h3 )
        self.addLink( s1, h4)

        # Add links between the switches
        self.addLink( s1, s2 )
        self.addLink( s2, s3 )
        self.addLink( s3, s1 )

class NetworkTest():
    def __init__(self, controller_ip):
        # Create an instance of our topology
        mininet.clean.cleanup()
        topo = RingTopo()

        # Create a network based on the topology using OVS and controlled by
        # a remote controller.
        patch('mininet.util.fixLimits', side_effect=None)
        self.net = Mininet(
            topo=topo,
            controller=lambda name: RemoteController(
                                        name, ip=controller_ip, port=6653),
            switch=OVSSwitch,
            autoSetMacs=True )

    def start(self):
        self.net.start()
        self.start_controller(clean_config=True)

    def start_controller(self, clean_config=False):
        # restart kytos and check if the napp is still disabled
        try:
            with open('/var/run/kytos/kytosd.pid', "r") as f:
                pid = int(f.read())
                os.kill(pid, signal.SIGTERM)
            time.sleep(5)
        except Exception as e:
            print "FAIL restarting kytos -- %s" % (e)
            pass
        if clean_config:
            # TODO: config is defined at NAPPS_DIR/kytos/storehouse/settings.py 
            # and NAPPS_DIR is defined at /etc/kytos/kytos.conf
            os.system('rm -rf /var/tmp/kytos/storehouse')
        os.system('kytosd')

    def wait_switches_connect(self):
        max_wait = 0
        while any(not sw.connected() for sw in self.net.switches):
            time.sleep(1)
            max_wait += 1
            if max_wait > 30:
                raise TimeoutError

    def stop(self):
        self.net.stop()
        mininet.clean.cleanup()
