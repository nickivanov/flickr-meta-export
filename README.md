From the **Settings** page click **Request my Flickr data**. In a day or two you
will receive an email with two links, one for the metadata archive and another for
the image archive.

Extract the two archives, which will create two directories, one containing metadata
and another containing images.


The process might look like this:

1. Update tag mapping (optional).

You can update the mapping of Flickr metadata properties to EXIF/XMP/IPTC image 
tags if you want. A sample mapping file, `map.json` is provided. Its `input_tags`
properties contains a JSON array of strings that correspond to the Flickr metadata
properties, and the `output_tags` array contains the image tags to be set. Output 
tags can contain group name, e.g. `"EXIF:Make"`, following the ExifTool tag syntax.

Example input tag specifications and JSON they match:

- `"name"`
   Matches `{"name": "foobar"}`

- `"exif.Make"`
   Matches `{"exif": {"Make": "samsung"}}`

- `"albums[0].name"`
   Matches the `name` property of the first `albums` element, that is, will return
   `"album1"` given the following input: 
   `{"albums": [{"name": "album1"}, {"name": "album2"}]}

- `"tags[*].tag"`
   Matches the `tag` property of all `tags` element then joins them in a single
   string, separated by spaces. This will return `"foo bar"` given the following input: 
   `{"tags": [{"tag": "foo"}, {"tag": "bar"}]}

- `"exif.Make=foobar"`
   Supplies the default value for `"exif.Make"`, that is, will return `"foobar"`
   if there is no `Make` in `exif` or if there's no `exif`.


2. Extract Flickr metadata.

Flickr metadata does not follow any standard image metadata format, and I'm 
using Phil Harvey's [ExifTool](https://www.sno.phy.queensu.ca/~phil/exiftool/) to
update image files. As the first step I convert Flickr metadata into a format
ExifTool can consume -- a CSV file. This is where the Python program comes in.

    PYTHONIOENCODING=utf-8 \
    IMG_DIR=/path/to/image/files TAG_MAP=./map.json \
    ./meta2csv.py "/path/to/metadata/files/photo_*json" \
    >/path/to/image/files/meta.csv

Note that you need to put the metadata file pattern in quotes to avoid the shell 
globbing.

For example:

```
PYTHONIOENCODING=utf-8 \
IMG_DIR=/Volumes/media/downloads/data-download-1 TAG_MAP=./map.json \
./meta2csv.py "/Volumes/media/downloads/flickr-export/meta/photo_*json" \
>/Volumes/media/downloads/data-download-1/meta.csv
```

Two environment variables that control the program behaviour are:

- `IMG_DIR`: Indicates the directory path where the actual image files have been
  extracted from the Flickr export. If not specified the current directory is assumed.

- `TAG_MAP`: Points to the customized tag map file. If not specified, the default
  mapping hard-coded in the program is used.

Set `PYTHONIOENCODING` if any of your Flickr metadata -- image titles, descriptions,
tags etc. -- contain non-ASCII characters, otherwise Python stdout redirection 
will fail to print such characters.

3. Update image metadata with ExifTool.

Once the Flickr metadata is saved in a CSV file that can be understood by ExifTool,
you can update the image files. The command below will read the CSV file created
in the previous step, update each matching file's metadata with tags from that 
CSV file, and copy the file into a directory named after the Flickr album it belongs to.

It should run from the directory where image files have been extracted. 

    /path/to/exiftool -csv=<CSV file name> -e jpg -e png .

4. Separate images into albums.

Optionally you can now sort your images into directories based on the Flickr albums 
they were in. Note that if any of your images belongs to multiple albums on Flickr,
only the first album will be used to set the image metadata in step 2 above.

    /path/to/exiftool -'Directory<Album' -o %f.%e -e jpg -e png .

Note that this command will create a new subdirectory for each Flickr album; make sure 
that you run it from the directory where you want these album subdirectories to 
be created.