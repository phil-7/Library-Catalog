from libzim.reader import Archive

zim = Archive("data/ekopedia_fr_all_nopic_2021-03.zim")
entry = zim.main_entry
item = entry.get_item()

print("Item methods:")
for name in dir(item):
    print(" -", name)
