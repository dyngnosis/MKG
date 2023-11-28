#make_cmd.py

fams = ["Akira",
"AlphV_BlackCat",
"AlphV_Sphynx",
"AsyncRat",
"Blacksuit",
"BruteRatel",
"Bumblebee",
"Cl0p",
"CobaltStrike",
"DCRat",
"Emotet",
"FormBook",
"GootLoader",
"GuLoader",
"Havoc",
"IcedID",
"Lockbit",
"Metasploit",
"NjRat",
"OrcusRat",
"P2PInfect",
"Phobos",
"Play",
"QuasarRat",
"RacoonStealer",
"Raspberry_Robin",
"Redline",
"Remcos",
"SmokeLoader",
"SocGholish_FakeUpdates",
"Symbiote",
"System BC",
"Truebot",
"Vidar",
"XWorm"]

for f in fams:
    grepstring = f.replace("_", " ")
    #print(grepstring)
    cmd = f"mkdir -p data_input/{f}_reports && mkdir -p data_output/{f}_reports && grep -l '{grepstring}' data_input/mw_reports/* | xargs -I {{}} cp {{}} data_input/{f}_reports ; python tool.py {f}"
    print(cmd)
    