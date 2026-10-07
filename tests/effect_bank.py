def decode(r,start=0x15517e):
 out=bytearray();p=start
 while True:
  end=p+int.from_bytes(r[p:p+2],'little');p+=2
  while p<end:
   cmd=r[p];p+=1
   if cmd&128:
    n=((cmd&96)>>5)+4;distance=((cmd&31)<<8)|r[p];p+=1
    for _ in range(n):out.append(out[-distance])
    while p<end and r[p]&224==96:
     n=r[p]&31;p+=1
     for _ in range(n):out.append(out[-distance])
   elif cmd&64:
    n=cmd&31
    if n&16:n=((n&15)<<8)|r[p];p+=1
    out.extend(bytes([r[p]])*(n+4));p+=1
   else:
    n=cmd&63
    if n&32:n=((n&31)<<8)|r[p];p+=1
    out.extend(r[p:p+n]);p+=n
  more=r[p];p+=1
  if not more:return bytes(out)
