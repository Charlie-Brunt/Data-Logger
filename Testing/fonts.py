from matplotlib import font_manager

print("List of all fonts currently available in the matplotlib:")
# print(*font_manager.findSystemFonts(fontpaths=None, fontext='ttf'), sep=" ")
print(*font_manager.get_font_names())