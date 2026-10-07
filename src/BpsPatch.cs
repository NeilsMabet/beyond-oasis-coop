using System;
using System.IO;
public static class BeyondOasisBps {
    static uint Crc(byte[] data, int length) {
        uint crc=0xffffffffu;
        for (int i=0;i<length;i++) {
            crc^=data[i];
            for(int bit=0;bit<8;bit++) crc=(crc>>1)^((crc&1)!=0?0xedb88320u:0u);
        }
        return crc^0xffffffffu;
    }
    static long Number(byte[] data,ref int pos,int end) {
        long value=0,shift=1;
        while(true) {
            if(pos>=end || shift>(1L<<49)) throw new InvalidDataException("Invalid BPS integer");
            int b=data[pos++];value=checked(value+(b&127)*shift);
            if((b&128)!=0)return value;
            shift<<=7;value=checked(value+shift);
        }
    }
    public static byte[] Apply(byte[] source,byte[] patch) {
        if(patch.Length<19 || patch[0]!=66 || patch[1]!=80 || patch[2]!=83 || patch[3]!=49)
            throw new InvalidDataException("Invalid BPS1 header");
        int end=patch.Length-12,pos=4;
        if(Crc(patch,patch.Length-4)!=BitConverter.ToUInt32(patch,patch.Length-4))
            throw new InvalidDataException("BPS checksum mismatch");
        if(Crc(source,source.Length)!=BitConverter.ToUInt32(patch,end))
            throw new InvalidDataException("BPS source checksum mismatch");
        long sourceSize=Number(patch,ref pos,end),targetSize=Number(patch,ref pos,end),metadata=Number(patch,ref pos,end);
        if(sourceSize!=source.Length || targetSize>Int32.MaxValue || metadata>end-pos)
            throw new InvalidDataException("Invalid BPS sizes");
        pos+=checked((int)metadata);
        byte[] target=new byte[checked((int)targetSize)];
        long output=0,sourceOffset=0,targetOffset=0;
        while(output<target.Length) {
            long action=Number(patch,ref pos,end),length=(action>>2)+1;
            if(length>target.Length-output)throw new InvalidDataException("BPS output overflow");
            int count=checked((int)length),at=checked((int)output);
            switch((int)(action&3)) {
            case 0:
                if(output+length>source.Length)throw new InvalidDataException("BPS source overflow");
                Array.Copy(source,at,target,at,count);break;
            case 1:
                if(length>end-pos)throw new InvalidDataException("BPS literals overflow");
                Array.Copy(patch,pos,target,at,count);pos+=count;break;
            case 2: {
                long delta=Number(patch,ref pos,end);
                sourceOffset=checked(sourceOffset+((delta&1)!=0?-(delta>>1):(delta>>1)));
                if(sourceOffset<0 || sourceOffset+length>source.Length)throw new InvalidDataException("BPS source copy overflow");
                Array.Copy(source,checked((int)sourceOffset),target,at,count);sourceOffset+=length;break;
            }
            case 3: {
                long delta=Number(patch,ref pos,end);
                targetOffset=checked(targetOffset+((delta&1)!=0?-(delta>>1):(delta>>1)));
                if(targetOffset<0 || targetOffset>=output)throw new InvalidDataException("BPS target copy overflow");
                for(int i=0;i<count;i++)target[at+i]=target[checked((int)targetOffset++)];
                break;
            }
            }
            output+=length;
        }
        if(pos!=end || Crc(target,target.Length)!=BitConverter.ToUInt32(patch,end+4))
            throw new InvalidDataException("BPS target checksum mismatch");
        return target;
    }
}
