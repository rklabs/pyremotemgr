#!/usr/bin/env python

import pexpect
import struct
import fcntl
import os
import sys
import signal
import datetime
import time
import pdb

EXPECT_TIMEOUT = 10;
READ_NB_TIMEOUT = 1

SSH_NEW_KEY_PROMPT = "Are you sure you want to continue connecting"
SSH_PASSWORD_PROMPT = "%s@%s\'s password:"
READ_SIZE = 1024 * 8

class SshSession( object ):
    def __init__( self, server, username, password ):
        self.server_ = server
        self.username_ = username
        self.password_ = password
        self.pSsh_ = None
        self.logfile_ = file( 'Test_' + str( datetime.datetime.now() ), 'w' )

    def connect( self ):
        cmd = "ssh %s@%s" % ( self.username_, self.server_ )
        # Spawn new ssh session
        self.pSsh_ = pexpect.spawn( cmd, logfile=self.logfile_ )

        # There are 4 cases to be handled here
        # 1. New key prompt(client is ssh'ing for the first time
        # 2. Password prompt
        # 3. EOF(indicating something went bad)
        # 4. The connection timed out
        ret = self.pSsh_.expect( [ SSH_NEW_KEY_PROMPT,
                                   SSH_PASSWORD_PROMPT % ( self.username_, self.server_ ),
                                   pexpect.EOF,
                                   pexpect.TIMEOUT ], EXPECT_TIMEOUT )
        # First time ssh to server
        if ret == 0:
            self.pSsh_.sendline( "yes" )
            ret = self.pSsh_.expect( [ SSH_NEW_KEY_PROMPT, "password:", pexpect.EOF ] )

        # Got password prompt
        if ret == 1:
            self.pSsh_.sendline( password )
        # Got EOF
        elif ret == 2:
            print "I either got key or connection timeout"
            pass
        # Got timeout
        elif ret == 3:
            pass

        # Send carriage return and expect prompt
        self.pSsh_.sendline( "\r" )
        self.pSsh_.expect( [ '>', 'config', 'enable' ] )

    def close( self ):
        self.pSsh_.close()
        self.logfile_.close()

    def sendCmd( self, cmd ):
        self.pSsh_.sendline( cmd )
        self.pSsh_.expect( '>' )

        # Sleep is necessary, sendline doesn't work without sleep,
        # it needs sometime to be able to send command and get output
        time.sleep(1)

        # Read as much output as possible
        output = ''
        endRead = False
        while not endRead:
            try:
                output += self.pSsh_.read_nonblocking( size=READ_SIZE,
                                                       timeout=READ_NB_TIMEOUT )
            except pexpect.TIMEOUT:
                endRead = True

        # The output consists of 3 sections
        # 1. cmd(which is echoed)
        # 2. actual output
        # 3. command prompt
        if cmd in output[0]:
            print 'Command has been echoed back'
        if '>' in output[-1]:
            print 'Got bash prompt'

        # Ignore first line which contains cmd echoed back and
        # last line which contains the command prompt
        actualOutput = output[1:-1]

        return actualOutput

    def __del__( self ):
        self.pSsh_.close()
        self.logfile_.close()

if __name__ == "__main__":
    username = "rkadam"
    password = "rkadam"
    server = "bs368"

    dutSession = SshSession( server, username, password )
    dutSession.connect()
    cmds = [ "w" ]

    for cmd in cmds:
        output = dutSession.sendCmd( cmd )
        print output

