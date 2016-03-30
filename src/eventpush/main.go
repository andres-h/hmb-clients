/***************************************************************************
 *   Copyright (C) by GFZ Potsdam                                          *
 *                                                                         *
 *   Author:  Andres Heinloo                                               *
 *   Email:   andres@gfz-potsdam.de                                        *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2, or (at your option)   *
 *   any later version. For more information, see http://www.gnu.org/      *
 ***************************************************************************/

package main

import (
	"bitbucket.org/andresh/httpmsgbus/apps/go/src/hmb"
	"bytes"
	"compress/zlib"
	"encoding/json"
	"flag"
	"io"
	_log "log"
	"log/syslog"
	"os"
	"os/exec"
)

const VERSION = "0.2 (2016.090)"

const (
	// Syslog facility.
	SYSLOG_FACILITY = syslog.LOG_LOCAL0

	// Syslog severity.
	SYSLOG_SEVERITY = syslog.LOG_NOTICE
)

// log is a global logger that can be switched to Syslog.
var log = _log.New(os.Stdout, "", _log.LstdFlags)

func main() {
	sink := flag.String("H", "", "Destination HMB URL")
	gnupghome := flag.String("g", "", "GnuPG home directory (default $HOME/.gnupg)")
	jsonfile := flag.String("j", "", "JSON metadata file")
	qmlfile := flag.String("q", "", "QuakeML XML data file")
	useSyslog := flag.Bool("s", false, "Log via syslog")
	timeout := flag.Int("t", 120, "HMB timeout in seconds")

	flag.Parse()

	if *sink == "" {
		log.Fatal("missing destination HMB URL")
	}

	if *jsonfile == "" {
		log.Fatal("missing JSON metadata file")
	}

	if *qmlfile == "" {
		log.Fatal("missing QuakeML XML data file")
	}

	// If Syslog is requested, re-assign the global log variable.
	if *useSyslog {
		if l, err := syslog.NewLogger(SYSLOG_FACILITY|SYSLOG_SEVERITY, 0); err != nil {
			log.Fatal(err)

		} else {
			log = l
		}
	}

	log.Printf("eventpush v%s started", VERSION)

	// The actual payload of the message.
	var data map[string]interface{}

	// First add all attributes from the JSON file.
	if r, err := os.Open(*jsonfile); err != nil {
		log.Fatal(err)

	} else {
		decoder := json.NewDecoder(r)

		if err := decoder.Decode(&data); err != nil {
			log.Fatal(err)
		}
	}

	// Now compress the QuakeML data and create a GPG signature.
	if r, err := os.Open(*qmlfile); err != nil {
		log.Fatal(err)

	} else {
		var bdata, bsig bytes.Buffer

		w := zlib.NewWriter(&bdata)

		if _, err := io.Copy(w, r); err != nil {
			log.Fatal(err)

		} else if err := w.Close(); err != nil {
			log.Fatal(err)
		}

		data["zquakeml"] = bdata.Bytes()

		args := []string{"--detach-sign"}

		if *gnupghome != "" {
			args = append(args, "--homedir")
			args = append(args, *gnupghome)
		}

		cmd := exec.Command("gpg", args...)
		cmd.Stdin = &bdata
		cmd.Stdout = &bsig

		if err := cmd.Run(); err != nil {
			log.Fatal(err)
		}

		data["signature"] = bsig.Bytes()
	}

	// Create HMB message with the payload.
	m := &hmb.Message{
		Type:  "QUAKEML_EVENT",
		Queue: "QUAKEML_EVENT",
		Data:  hmb.Payload{data},
	}

	// Add starttime and endtime, enabling time-based queries.
	if dateTime, ok := data["dateTime"]; !ok {
		log.Fatal("missing dateTime attribute")

	} else if dateTime, ok := dateTime.(string); !ok {
		log.Fatal("invalid dateTime attribute")

	} else {
		var t hmb.Time
		if err := t.UnmarshalText([]byte(dateTime)); err != nil {
			log.Fatal(err)
		}

		m.Starttime = t
		m.Endtime = t
	}

	// Create HMB client using given timeout and 10 seconds retry wait.
	h := hmb.NewClient(*sink, nil, &hmb.OpenParam{}, *timeout, 10, log)

	// Send the message. This function keeps retrying if a network error
	// occurs.
	if err := h.Send([]*hmb.Message{m}); err != nil {
		log.Fatal(err)
	}

	log.Println("message sent")
}
