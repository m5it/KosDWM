import zlib,re,os
#-- RANDOM
#
def rmatch(input,regex):
	x = re.match( regex, input )
	if x != None:
		return x
	else:
		return False
#
def crc32b(text):
	return "%x"%(zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF)
#-- FILE
#
def file_content(fn):
    print("file_content() starting fn: {}\n".format(fn))
    if os.path.isfile(fn)==False:
        print("file_content() failed, file missing.")
        return ""
    
    with open(fn) as f: 
        return f.read()
    f.close()
#
def file_exists( filename:str ) -> bool:
	return os.path.exists( filename )
