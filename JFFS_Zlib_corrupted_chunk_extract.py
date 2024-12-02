#!/usr/bin/env python3

#### Simple Script to extract possibly corrupted JFFS Chunks, currently only supports ZLIB and uncompressed data.
#### Carves out even "deleted" chunks , since JFFS is a log file system "normal" Tools like Jefferson only output the most recent fileversion.
#### Chunks can be extracted individual or concatenated.

import os
import io
import zlib
import mmap
import binascii

def mtd_crc(data):
    return (binascii.crc32(data, -1) ^ -1) & 0xFFFFFFFF

def decompress_corrupted(data):

        d = zlib.decompressobj() 
        f = io.BytesIO(data)
        result_str = b''
        buffer = f.read(1)
        try:
            while buffer:
                result_str += d.decompress(buffer)
                buffer = f.read(1)
        except zlib.error:
            pass
        return result_str

InputFile = open("Filename.bin", "rb")
data = InputFile.read()
InputFile_len = os.fstat(InputFile.fileno()).st_size

MemappedFile=mmap.mmap(InputFile.fileno(), InputFile_len, access=mmap.ACCESS_READ)

pos=0

indexold=-1
inodeold=-1
index=-1
tmpbuffer=bytearray()

enterNewInode=False

DoConcat=1
DoSingleInodeExtract=0
DoDecompNone=1
DoDecompZip=1
DetectedCRCError=0
ExtractMax=0

MultiDiffCNT=1

while (pos <= InputFile_len):

    print("index: " + str(index) + " indexold: " + str(indexold))
    print("-----------")
    index = MemappedFile.find(b'\x85\x19\x02\xE0',pos)
    if (index == -1 ): break

    print("index: " + str(index) + " indexold: " + str(indexold) + " SearchStartPos: " + str(pos) )
    print("Inode: " + str(int.from_bytes(MemappedFile[index+12:index+16],"little") ))
    print("Chunk: " + str(int.from_bytes(MemappedFile[index+16:index+20],"little") ))
    compmethodnext=MemappedFile[index+56]
    inode= int.from_bytes(MemappedFile[index+12:index+16],"little")
    
    ### CRC-Check
    GivenhdrCRC=(int.from_bytes(MemappedFile[index+8:index+12],"little"))
    GivenNodeCRC=(int.from_bytes(MemappedFile[index+64:index+68],"little"))

    nodeCRC=mtd_crc(MemappedFile[index:index+60])
    hdrCRC=mtd_crc(MemappedFile[index:index+8])

    if (nodeCRC!=GivenNodeCRC) or (hdrCRC!=GivenhdrCRC): 
        print("!!! CRC _ ERROR !!!")
        DetectedCRCError=1

    if (inode!=inodeold and pos>0): 
        enterNewInode=True
        print(enterNewInode)

    ## decompress deflate zlib
    if (indexold != -1 and compmethodold==6 and DoDecompZip): 
        print("DataField: " + str(indexold+68) + " to " + str(index))
        if (ExtractMax): decomp_data=decompress_corrupted(MemappedFile[indexold+68:index])
        else: decomp_data=decompress_corrupted(MemappedFile[indexold+68:indexold+68+(int.from_bytes(MemappedFile[indexold+52:indexold+56],"little"))])

        if len(decomp_data) > 0:        

            if (DoConcat):
                nameconcat = "CONCATDecompressedOut_"  + str(MultiDiffCNT) + "_" + str(inodeold)
                concatfile = open(nameconcat, "ab")
                concatfile.write(decomp_data)

            if (DoSingleInodeExtract):
                name = "DecompressedOut_" + str(inodeold) + "_" + str(chunkold) + "_" + str(indexold)
                tempfile = open(name, "wb")
                tempfile.write(decomp_data)
                tempfile.close

            if (enterNewInode):
                if (DoConcat): concatfile.close
                MultiDiffCNT+=1
                enterNewInode=False
    
    #### Handle uncompressed chunks
    if (indexold != -1 and compmethodold==0 and DoDecompNone): 
        print("DataField: " + str(indexold+68) + " to " + str(index))
        print("Datasize: " + str((int.from_bytes(MemappedFile[indexold+52:indexold+56],"little"))))

        if (ExtractMax): decomp_data=MemappedFile[indexold+68:index]
        else: decomp_data=MemappedFile[indexold+68:indexold+68+(int.from_bytes(MemappedFile[indexold+52:indexold+56],"little"))]

        if len(decomp_data) > 0:        
            name = "DecompressedOut_" + str(inodeold) + "_" + str(chunkold) + "_" + str(indexold)

            if (DoConcat):
                nameconcat = "CONCATDecompressedOut_"  + str(MultiDiffCNT) + "_" + str(inodeold)
                concatfile = open(nameconcat, "ab")
                concatfile.write(decomp_data)

            if (DoSingleInodeExtract):
                name = "DecompressedOut_" + str(inodeold) + "_" + str(chunkold) + "_" + str(indexold)
                tempfile = open(name, "wb")
                tempfile.write(decomp_data)
                tempfile.close

            print("written... Bytes: " +   str(len(decomp_data)) + " " + name )
            print("inode " + str(inode) + "_" + "inodeold" + str(inodeold))
            if (enterNewInode):
                if (DoConcat): concatfile.close
                MultiDiffCNT+=1
                enterNewInode=False

    indexold=index
    compmethodold=compmethodnext
    inodeold=(int.from_bytes(MemappedFile[index+12:index+16],"little"))
    chunkold=(int.from_bytes(MemappedFile[index+16:index+20],"little"))

    pos = index+4

    if (DetectedCRCError):
        index=-1
        indexold=-1
        compmethodnext=-1
        compmethodold=-1
        DetectedCRCError=0
    


