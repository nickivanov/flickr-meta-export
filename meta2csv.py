#!/usr/bin/env python
"""Convert Flickr metadata from JSON to CSV.

Metadata is exported by the _Request my Flickr data_ function on your profile
page on Flickr. It is saved as a series of JSON files, one for each photo. This
program will convert all these JSON files into a single CSV file, according
to the supplied mapping. The CSV file can then be used by [ExifTool](https://www.sno.phy.queensu.ca/~phil/exiftool/) to update
image EXIF/XMP/whatever metadata.

The program accepts one command line argument: path to the metadata files. Enclose
the pattern in quotes to avoid shell globbing.

Options that can be set via environment variables:

`IMG_DIR`: Indicates the directory path where the actual image files have been
extracted from the Flickr export. If not specified the current directory is assumed.

`TAG_MAP`: Points to the customized tag map file. If not specified, the default
mapping hard-coded in the program is used.

Prints CSV data to standard output. Set the environment variable `PYTHONIOENCODING`
when redirecting to a file if your metadata is known to contain non-ASCII characters.

"""

from __future__ import print_function
import glob
import json
import logging
import os
import re
import sys
from os.path import basename

# Default property mapping
input_tags = [
  "name",
  "description",
  "albums[0].title=unknown",
  "tags[*].tag",
  "date_imported"
  ,"license"
]
output_tags = [
  "Name",
  "Description",
  "Album",
  "Keywords"
  ,"DateTimeDigitized"
  ,"UsageTerms"
]

img_dir = "."

if "DEBUG" in os.environ:
  logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("meta2csv")

def get_element(obj, index):
  """Return the specified list element
  Arguments:
  obj -- List or tuple object.
  index -- Index of the element to return.
  """
  logger.debug("get_element: obj=%r, index=%r", obj, index)
  try:
    index = int(index)
  except TypeError:
    return ""
  if isinstance(obj, list) or isinstance(obj, tuple):
    if index < len(obj):
      return obj[int(index)]
    else:
      return ""
  else:
    return ""

def get_property(obj, prop):
  """Return the specified list element
  Arguments:
  obj -- Dict object.
  index -- Key of the element to return.
  
  Examples of keys:

  - "name": Matches {"name": "foobar"}

  - "exif.Make": Matches {"exif": {"Make": "samsung"}}

  - "albums[0].name": Matches the name property of the first albums element, 
    that is, will return "album1" given the input: 
    {"albums": [{"name": "album1"}, {"name": "album2"}]}

  - "tags[*].tag": Matches the tag property of all tags element then joins them 
    in a single string, separated by spaces. This will return "foo bar" given the input: 
    {"tags": [{"tag": "foo"}, {"tag": "bar"}]}

  - "exif.Make=foobar": Supplies the default value for "exif.Make", that is, will 
    return "foobar" if there is no "Make" in "exif" or if there's no "exif".
  """
  logger.debug("get_property: obj=%r, prop=%r", obj, prop)
  if not prop:
    return ""

  return_value = ""
  default_value = ""

  # see if there's a default provided
  if "=" in prop:
    dft_parts = prop.split("=")
    if len(dft_parts) == 2:
      prop = dft_parts[0]
      default_value = dft_parts[1]

  if not "." in prop: 
    if "[" in prop: # this shouldn't happen but...
      listparts = re.split(r"[\[\]]", prop) 
      return_value = get_element(get_property(obj, listparts[0]), listparts[1])
    else:
      if isinstance(obj, dict) and prop in obj:
          return_value = obj[prop]
  else: # multipart property name
    parts = prop.split(".")

    # check if first element refers to a list
    if "[" in parts[0]: # list/tuple reference
      listparts = re.split(r"[\[\]]", parts[0])
      if listparts[1] == "*": # special case
        list_obj = get_property(obj, listparts[0])
        if isinstance(list_obj, list) or isinstance(list_obj, tuple): # it is indeed a list
          # retrieve the child property from each list item, join together
          return_value = " ".join([get_property(item, ".".join(parts[1:])) for item in list_obj])
      else: # retrieve the specified element
        return_value = get_property(
          get_element(
            get_property(obj, listparts[0]),
            listparts[1]
          ),
          ".".join(parts[1:])
        )
    else:
      return_value = get_property(get_property(obj, parts[0]), ".".join(parts[1:]))
    
    if not return_value and default_value:
      return_value = default_value
    
  return return_value

def main(pattern):

  logger.debug("stdout encoding = %s", sys.stdout.encoding)
  # Add an extra field for ExifTool
  output_tags.insert(0, "SourceFile")

  # print header
  print(",".join(output_tags))

  # process each file
  for f in glob.glob(pattern):
    meta = json.load(open(f))
    logger.debug("Loaded metadata %r", meta)
    # exported filenames have little common with metadata, look up by id
    file_id = meta["id"]
    img_list = glob.glob("%s/*%s*" % (img_dir, file_id))
    if img_list:
      # here's to hoping that id is unique; if not, grab the "first" one
      fields = [img_list[0]]
      for t in input_tags:
        fields.append(get_property(meta, t))
      logger.debug("Fields: %r", fields)
      out_line = ",".join('"%s"' % s for s in fields)
      logger.debug("Will print: %s", out_line)
      print(out_line)
    else:
      logger.debug("Image with id %s not found", file_id)


if __name__ == "__main__":

  if len(sys.argv) < 2:
    print("No file or pattern provided")
    sys.exit()

  # by default we think images are in the current directory but this can be
  # overridden
  if "IMG_DIR" in os.environ:
    img_dir = os.environ["IMG_DIR"]

  if "TAG_MAP" in os.environ:
    map_file = os.environ["TAG_MAP"]
    if os.path.isfile(map_file):
      new_map = json.load(open(map_file))
      if "input_tags" in new_map and "output_tags" in new_map:
        input_tags = new_map["input_tags"]
        output_tags = new_map["output_tags"]

  main(sys.argv[1])