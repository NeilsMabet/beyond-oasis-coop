import ctypes as C
import sys, pathlib, hashlib, json
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
PACKAGE = ROOT.parent
ROM = pathlib.Path(r'C:\Neuro\Beyond Oasis project\Beyond Oasis (U) [!].bin')
class Game(C.Structure):
    _fields_ = [('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
class Variable(C.Structure):
    _fields_ = [('key',C.c_char_p),('value',C.c_char_p)]

class Core:
    def __init__(self, rom=ROM, debug=False, core_path=None):
        self.dll=C.CDLL(str(core_path or PACKAGE/('core/debug_libretro.dll' if debug else 'core/genesis_plus_gx_libretro.dll')))
        self.capture=True
        self.buttons=[set(),set()]; self.frame=0; self.picture=None; self.fmt=0
        self.options={b'genesis_plus_gx_region_detect':b'ntsc-u',b'genesis_plus_gx_padtype':b'3-buttons'}
        self.strings=[]
        self.defaults={}
        def environment(cmd,data):
            if cmd==10: self.fmt=C.cast(data,C.POINTER(C.c_int))[0]; return True
            if cmd in (3,18): return False
            if cmd in (9,31):
                s=C.create_string_buffer(str(ROOT).encode());self.strings.append(s)
                C.cast(data,C.POINTER(C.c_char_p))[0]=C.cast(s,C.c_char_p);return True
            if cmd==15:
                v=C.cast(data,C.POINTER(Variable)).contents
                if v.key in self.options: v.value=self.options[v.key];return True
                v.value=self.defaults.get(v.key)
                return v.value is not None
            if cmd==16:
                variables=C.cast(data,C.POINTER(Variable));i=0
                while variables[i].key:
                    definition=variables[i].value
                    self.defaults[variables[i].key]=definition.split(b"; ",1)[1].split(b"|",1)[0]
                    i+=1
                return True
            if cmd==17: C.cast(data,C.POINTER(C.c_bool))[0]=False;return True
            if cmd==52: C.cast(data,C.POINTER(C.c_uint))[0]=0;return True
            if cmd==65583: C.cast(data,C.POINTER(C.c_int))[0]=7;return True
            return False
        def video(ptr,w,h,pitch):
            if not ptr or not self.capture:return
            raw=C.string_at(ptr,pitch*h)
            if self.fmt==1:
                a=np.frombuffer(raw,np.uint8).reshape(h,pitch)[:,:w*4].reshape(h,w,4)
                self.picture=a[:,:,[2,1,0]].copy()
            else:
                a=np.frombuffer(raw,'<u2').reshape(h,pitch//2)[:,:w]
                if self.fmt==2:r,g,b=(a>>11)*255//31,((a>>5)&63)*255//63,(a&31)*255//31
                else:r,g,b=((a>>10)&31)*255//31,((a>>5)&31)*255//31,(a&31)*255//31
                self.picture=np.stack([r,g,b],axis=-1).astype(np.uint8)
        types=[(C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p),environment,'retro_set_environment'),
               (C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t),video,'retro_set_video_refresh'),
               (C.CFUNCTYPE(None,C.c_int16,C.c_int16),lambda l,r:None,'retro_set_audio_sample'),
               (C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t),lambda p,n:n,'retro_set_audio_sample_batch'),
               (C.CFUNCTYPE(None),lambda:None,'retro_set_input_poll'),
               (C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint),lambda p,d,i,b:int(p<2 and b in self.buttons[p]),'retro_set_input_state')]
        self.callbacks=[]
        for typ,func,name in types:
            cb=typ(func); self.callbacks.append(cb); getattr(self.dll,name)(cb)
        self.dll.retro_init()
        self.data=C.create_string_buffer(pathlib.Path(rom).read_bytes())
        self.dll.retro_load_game.argtypes=[C.POINTER(Game)];self.dll.retro_load_game.restype=C.c_bool
        assert self.dll.retro_load_game(C.byref(Game(str(rom).encode(),C.cast(self.data,C.c_void_p),len(self.data)-1,None)))
        self.dll.retro_set_controller_port_device(0,1);self.dll.retro_set_controller_port_device(1,1)
        self.dll.retro_get_memory_data.argtypes=[C.c_uint];self.dll.retro_get_memory_data.restype=C.c_void_p
        self.dll.retro_get_memory_size.argtypes=[C.c_uint];self.dll.retro_get_memory_size.restype=C.c_size_t
        self.dll.retro_serialize_size.restype=C.c_size_t
        self.dll.retro_serialize.argtypes=[C.c_void_p,C.c_size_t];self.dll.retro_serialize.restype=C.c_bool
        self.dll.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t];self.dll.retro_unserialize.restype=C.c_bool
    def run(self,n,one=(),two=()):
        self.buttons=[set(one),set(two)]
        for _ in range(n): self.dll.retro_run();self.frame+=1
    def ram(self):
        raw=C.string_at(self.dll.retro_get_memory_data(2),self.dll.retro_get_memory_size(2))
        return np.frombuffer(raw,np.uint8).reshape(-1,2)[:,::-1].copy().tobytes()
    def save(self,name):
        n=self.dll.retro_serialize_size();b=C.create_string_buffer(n);assert self.dll.retro_serialize(b,n)
        (ROOT/(name+'.state')).write_bytes(b.raw)
        (ROOT/(name+'.ram')).write_bytes(self.ram())
        if self.picture is not None:Image.fromarray(self.picture).save(ROOT/(name+'.png'))
    def load(self,name):
        data=(ROOT/(name+'.state')).read_bytes(); b=C.create_string_buffer(data);assert self.dll.retro_unserialize(b,len(data))
    def state(self):
        n=self.dll.retro_serialize_size();b=C.create_string_buffer(n);assert self.dll.retro_serialize(b,n);return b.raw
    def restore(self,data):
        b=C.create_string_buffer(data);assert self.dll.retro_unserialize(b,len(data))

if __name__=='__main__':
    c=Core()
    for n,buttons,name in [(180,(),'boot'),(1,(3,),'start'),(180,(),'menu'),(1,(0,),'confirm'),(300,(),'intro'),(1,(3,),'skip'),(300,(),'game')]:
        c.run(n,buttons);c.save(name);print(name,c.frame,flush=True)




