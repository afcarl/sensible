with open('csmlog_1479402620.txt', 'r') as f:
    c = f.read().split("CSM Tx...")
    for i in c:
        print(i)
