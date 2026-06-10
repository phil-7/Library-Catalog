# from libzim.reader import Archive

# # Path to your ZIM file
# zim_path = "data/ekopedia_fr_all_nopic_2021-03.zim"

# # Open the archive
# zim = Archive(zim_path)

# # --- Basic metadata ---
# print("Main page path:", zim.main_entry.get_item().path)
# print("UUID:", zim.uuid)
# print("Title:", zim.title)
# print("Description:", zim.description)
# print("Language:", zim.language)
# print("Article count:", zim.article_count)
# print("Media count:", zim.media_count)
# print("Checksum:", zim.checksum)

# # --- Iterate entries (optional) ---
# print("\nListing first 20 entries:")
# for i, entry in enumerate(zim.iter_entries()):
#     if i >= 20:
#         break
#     print(f"{i+1}. {entry.title}  |  {entry.path}  |  {entry.mimetype}")
