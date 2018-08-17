# jpegdupes

jpegdupes is a command-line tool that finds duplicated images in a directory tree. The difference with other file-oriented utilities (like fdupes) is that jpegdupes is specifically tailored to JPEG files, and compares only the image data chunk, ignoring any metadata present in the file (EXIF info, tags, titles, orientation tag...). This makes possible to find duplicated images when one of the file's metadata has been modified by imaging software, and byte-by-byte comparators fail to report them as equal. This might happen in a number of situations, for example:

- Modifying EXIF info to adjust date taken (typically when the camera has been set at a wrong date/time)
- Adjusting rotation flag or rotating the photo losslessly (f. e. using jpegtran)
- Adding tags, or setting title, description, rating...
 
A common scenario that could lead to this kind of duplicates is importing a file, altering its metadata in some way (tag, rotate or whatever), and then re-importing it again because the image software isn't smart enough to realize that the modified image is the same than the original, unmodified file that it's in the camera. This kind of duplicates are annoying and hard to find, because standard file duplication utilities won't report them (they're actually different files), so human checking is almost always required. jpegdupes tries to automate this task.

Invocation of jpegdupes is intentionally similar to that of the UNIX command fdupes. This is just for clarity and ease of use, but jpegdupes is not meant as a direct replacement of fdupes, which is much more mature and well tested. The recommended usage is using fdupes first, to find and delete byte-by-byte duplicates, and only then using jpegdupes to look for duplicates that fdupes might have missed. Even if the interface is inspired by fdupes, not all fdupes parameters are implemented, though, and there're even some differences in global behaviour (i. e. recursive exploring is optional in fdupes, but mandatory in jpegdupes), so be sure to execute jpegdupes --help to check the details. A simple invocation of jpegdupes would be:

`jpegdupes path_to_your_image_collection`

It would start to recursively analyze the directory tree, and at the end it would show a list of the duplicates it might have found. If you use --delete parameter, it would instead ask you, for each set of duplicates, which one should be preserved, and delete the rest.

Analyzing each image chunk of data in order to compare and find duplicates is a time consuming task. So, in order to speed up future executions, jpegdupes creates a cache file inside the directory it's analyzing, containing the image signatures already generated. It's a small file, called ".signatures", and follows python pickle format. Anyway, if you don't feel comfortable with the idea of jpegdupes writing to your disk, the parameter "--clean" may be used, which assures that nothing will be written to disk. The price is that all images will need to be re-analyzed each time jpegdupes is executed, and with a big collection it might take a while.

WARNING: If migrating from a previous Python 2.x version of jpegdupes, you'll probably get a nasty error about encoding. Due to changes in Python 3 encoding management, signature files (.signatures) created with previous versions of jpegdupes aren't readable anymore, so you'll have to delete them and let jpegdupes regenerate them from scratch.

As a final disclaimer, jpegdupes is provided as is, and I can't be made responsible of any damages that might happen to your collection by using it. I use jpegdupes myself, so I'm reasonably confident that it works, and at the same time I'm the first interested in that it's free of bugs, but I can't make any guarantee of that. Keep also in mind that, even if jpegdupes reports that two files correspond to the same image, this might not necessarily mean that you have to delete one of them. It's up to you to decide which cases correspond to software mistakes (i. e. re-importing an existing image that had been already imported and tagged) and which ones are legitimate.

## Requirements

jpegdupes uses Python 3 since v2. The following external packages are required to execute jpegdupes:

* GExiv2: JPEG metadata reading
* jpeginfo: Not actually needed, but I've found a number of corrupt JPEG files that only jpeginfo has been able to detect. If jpegdupes finds it installed it will use it as an extra validation step, so if you find jpegdupes getting stuck at certain files, try installing jpeginfo in your system with apt or whatever.
 
All these packages are usually easily installable in any Linux distribution by using their own package managers. In Ubuntu, the following commands should install everything:

```
sudo apt-get install python3-dev libjpeg-dev gir1.2-gexiv2-0.10 jpeginfo
```
On Debian stretch libturbojpeg0-dev is required. For Arch Linux there are AUR packages [imgdupes](https://aur.archlinux.org/packages/imgdupes/) and [imgdupes-git](https://aur.archlinux.org/packages/imgdupes-git/).

## History

v2.0

Migration from Python 2 to 3
Packaged for Pypi distribution (and renamed to jpegdupes due to imgdupes already existing as another project)
A lot of minor tweaks by me and some very kind contributors (thanks plenaerts for his several contributions, lagerspetz for his ideas and tweaks in his own fork, and probably others I don't remember right now).

v1.2

 Added multi-cpu support
 Remove -r parameter. Calculation of all possible rotations is now mandatory
 Removed identify command as a hash method. It complicated things, and MD5 and CRC are faster and available everywhere.
 
v1.1

  Support for losslessly rotated image detection
  
v1.0

  Initial release
