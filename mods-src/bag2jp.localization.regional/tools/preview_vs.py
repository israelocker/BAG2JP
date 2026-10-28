import sys,os,json
from PIL import Image, ImageChops
D=os.path.expanduser('~/work/vs/vs_hd'); M=json.load(open(f'{D}/layout.json'))
SX,SY=M['sx'],M['sy']
def L(n): return Image.open(f'{D}/{n}.png').convert('RGBA')
def put(cv,im,x,y): cv.alpha_composite(im,(round(x*SX),round(y*SY)))
def add(cv,im,x,y):
    X,Y=round(x*SX),round(y*SY); reg=cv.crop((X,Y,X+im.width,Y+im.height)).convert('RGB')
    a=im.getchannel('A'); rgb=Image.merge('RGB',[ImageChops.multiply(c,a) for c in im.convert('RGB').split()])
    cv.paste(ImageChops.add(reg,rgb).convert('RGBA'),(X,Y))
def compose(p1,p2,d1=1,d2=1):
    cv=Image.new('RGBA',(2048,1536),(0,0,0,255))
    put(cv,L('flames_blue'),256,0); put(cv,L('flames_red'),0,0)
    put(cv,L(f'c{p2:02d}_p2'),256,0); put(cv,L(f'c{p1:02d}_p1'),0,0)
    vw,vh=M['vs']; put(cv,L('vs'),256-vw//2,204-vh//2)
    if p2==11: add(cv,L('c11_p2x'),300,44)
    if p2==13: add(cv,L('c13_p2x'),304,0)
    n=M['chars'][str(p2)]['name']; put(cv,L(f'c{p2:02d}_name{d2}'),400-n[0]//2,204-n[1]//2)
    if p1==11: add(cv,L('c11_p1x'),98,44)
    if p1==13: add(cv,L('c13_p1x'),6,0)
    n=M['chars'][str(p1)]['name']; put(cv,L(f'c{p1:02d}_name{d1}'),112-n[0]//2,204-n[1]//2)
    return cv
a,b=int(sys.argv[1]),int(sys.argv[2])
compose(a,b).convert('RGB').resize((1024,768),Image.LANCZOS).save(sys.argv[3])
