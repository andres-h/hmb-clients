Installation
============

Install Go from https://golang.org/dl/

then:
::
  export GOPATH=`pwd`
  go get -u bitbucket.org/andresh/hmb-clients/src/eventpush

eventpush will be automatically compiled and installed in $GOPATH/bin

Managing GPG keys
=================

Data must to be signed with GPG. For this purpose you have to create a GPG
signing key with empty passphrase using "gpg --gen-key". Export the public
key using "gpg --export -a" and send to other parties, so they can verify
your signature.

Import public keys of other trusted parties using "gpg --import" and sign
those keys with "gpg --edit-key" (enter command "sign"), so they are fully
trusted.

Invoking eventpush
==================

eventpush needs a metadata file in JSON format (-j), a quakeml XML file
(-q) and an HMB URL (-H) to push the event to. Optionally the GPG home
directory (-g) can be specified.

The metadata should contain standard GDACS attributes, eg.:
::
  {
      "eventID": "gfz2016ftod", 
      "magnitude": 4.0, 
      "latitude": 34.95, 
      "longitude": 33.78, 
      "depth": 52.0, 
      "dateTime": "2016-03-22T20:24:21Z", 
      "status": "Reviewed", 
      "reliabilityCode": "M", 
      "location": "Cyprus Region", 
      "client": "GFZ" 
  }

Other attributes can be added as needed.
