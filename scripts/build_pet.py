"""Package source-pixel poses and the unmodified original movement animation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
import json, hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/gugu-pig'
PRE=ROOT/'previews'
FRAME=ROOT/'frames'
for p in [OUT,PRE,FRAME]: p.mkdir(parents=True,exist_ok=True)
STATES=['idle','running-right','running-left','waving','jumping','failed','waiting','running','review']
LABELS=['待机 · 睡个小觉','右移 · 原版像素猪','左移 · 原版像素猪','互动 · 动动耳朵','跳跃 · 开心弹跳','哭哭 · 闭眼掉眼泪','等待 · 等你回应','工作 · 努力敲电脑','检查 · 双眼一起眨']
COUNTS=[6,8,8,4,5,8,6,6,6]
DURATIONS=[[1680,660,660,840,840,1920],[120]*7+[220],[120]*7+[220],[140]*3+[280],[140]*4+[280],[140]*7+[240],[150]*5+[260],[120]*5+[220],[150]*5+[280]]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)

from pixel_animation import build
pixel_states,pixel_looks=build()

allframes=[]
atlas=Image.new('RGBA',(1536,2288))
# Original GIF is used directly, retaining all eight frames and the original
# internal displacement. Only one common nearest-neighbour scale is applied.
original=Image.open(ROOT/'sources/像素猪.gif')
original_frames=[]
for i in range(original.n_frames):
    original.seek(i); original_frames.append(original.convert('RGBA').copy())
assert len(original_frames)==8
source_bounds=[f.getbbox() for f in original_frames]
union=(min(b[0] for b in source_bounds),min(b[1] for b in source_bounds),max(b[2] for b in source_bounds),max(b[3] for b in source_bounds))
run_size=(round((union[2]-union[0])*.45),round((union[3]-union[1])*.45))
source_run=[]
for f in original_frames:
    sprite=f.crop(union).resize(run_size,Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(192,208)); frame.alpha_composite(sprite,((192-run_size[0])//2,176-run_size[1]))
    source_run.append(frame)
state_source={0:0,3:1,4:2,5:3,6:4,7:5,8:6}
for r,count in enumerate(COUNTS):
    frames=[]
    for c in range(count):
        baseline=174
        if r==4: baseline=[177,151,125,150,176][c]
        if r in state_source:
            frame=pixel_states[r][c]
        if r==1: frame=source_run[c].copy()
        if r==2: frame=ImageOps.mirror(source_run[c])
        frame.save(FRAME/f'{STATES[r]}-{c:02}.png')
        atlas.alpha_composite(frame,(192*c,208*r)); frames.append(frame)
    allframes.append(frames)

lookframes=[]
for n in range(16):
    f=pixel_looks[n]
    f.save(FRAME/f'look-{n:02}.png'); lookframes.append(f)
    atlas.alpha_composite(f,((n%8)*192,(9+n//8)*208))
atlas.save(OUT/'spritesheet.webp',lossless=True,method=6,exact=True)
atlas.save(PRE/'spritesheet.png')
manifest={'id':'gugu-pig','displayName':'咕咕猪 · 像素搭子','description':'待机睡觉、原版像素步态，开心眯眼跳、委屈闭眼哭的咕咕猪。','spriteVersionNumber':2,'spritesheetPath':'spritesheet.webp'}
(OUT/'pet.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Provide a v1 fallback with the same nine animation rows.
legacy=ROOT/'dist/gugu-pig-v1'; legacy.mkdir(exist_ok=True)
atlas.crop((0,0,1536,1872)).save(legacy/'spritesheet.webp',lossless=True,method=6,exact=True)
m={**manifest,'id':'gugu-pig-v1','displayName':'咕咕猪 · 兼容版','spriteVersionNumber':1}
(legacy/'pet.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def background(frame,color):
    im=Image.new('RGBA',frame.size,color); im.alpha_composite(frame); return im.convert('RGB')

for state,frames,ds in zip(STATES,allframes,DURATIONS):
    frames[0].save(PRE/(state+'.webp'),save_all=True,append_images=frames[1:],duration=ds,loop=0,lossless=True)
    fg=[background(f,'#f0ece4') for f in frames]
    fg[0].save(PRE/(state+'.gif'),save_all=True,append_images=fg[1:],duration=ds,loop=0,disposal=2)

# Labelled contact sheet, actual frame size on alternating light/dark rows.
contact=Image.new('RGB',(8*192,11*238),'#f0ece4'); dr=ImageDraw.Draw(contact)
for r in range(11):
    color='#f0ece4' if r%2==0 else '#202733'
    dr.rectangle((0,r*238,1535,(r+1)*238),fill=color)
    label=LABELS[r] if r<9 else ('观察方向 0°–157.5°' if r==9 else '观察方向 180°–337.5°')
    dr.text((14,r*238+5),label,font=font,fill='#252b32' if r%2==0 else '#ece7dc')
    fs=allframes[r] if r<9 else lookframes[(r-9)*8:(r-8)*8]
    for c,f in enumerate(fs): contact.paste(f,(c*192,r*238+30),f)
contact.save(PRE/'contact-sheet.jpg',quality=95)
directions=Image.new('RGB',(4*192,4*232),'#202733'); d=ImageDraw.Draw(directions)
for n,f in enumerate(lookframes):
    directions.paste(f,((n%4)*192,(n//4)*232+24),f)
    d.text(((n%4)*192+10,(n//4)*232+5),f'{n*22.5:g}°',font=small,fill='white')
directions.save(PRE/'directions.jpg',quality=95)

def active_index(t,ds):
    t=t%sum(ds)
    for j,d in enumerate(ds):
        if t<d: return j
        t-=d
    return len(ds)-1

# A compact 3x3 simultaneous animation preview.
gallery=[]
for t in range(0,8400,70):
    board=Image.new('RGB',(660,744),'#151c26'); d=ImageDraw.Draw(board)
    for r in range(9):
        x=(r%3)*220; y=(r//3)*248
        d.rounded_rectangle((x+5,y+5,x+214,y+241),radius=14,fill='#242e3b')
        f=allframes[r][active_index(t,DURATIONS[r])]
        board.paste(f,(x+14,y+20),f)
    gallery.append(board)
gallery[0].save(PRE/'all-actions.gif',save_all=True,append_images=gallery[1:],duration=70,loop=0,optimize=True)
gallery[0].save(PRE/'cover.png')
(ROOT/'animation.json').write_text(json.dumps({'states':STATES,'labels':LABELS,'counts':COUNTS,'durations':DURATIONS,'lookDirections':[i*22.5 for i in range(16)]},ensure_ascii=False,indent=2),encoding='utf-8')

report={'appVersion':'26.915.4065.0','formatVersion':2,'size':list(atlas.size),'cell':[192,208],'expectedFrames':sum(COUNTS)+16,'checks':{},'frames':[]}
checks=report['checks']
checks['manifest']=json.loads((OUT/'pet.json').read_text(encoding='utf8'))==manifest
decoded=Image.open(OUT/'spritesheet.webp').convert('RGBA')
checks['losslessRoundtrip']=np.array_equal(np.array(decoded),np.array(atlas))
checks['unusedCellsTransparent']=True
checks['allRequiredFramesPresent']=True
checks['safeMargins']=True
checks['binaryAlpha']=set(np.unique(np.array(decoded)[:,:,3])).issubset({0,255})
checks['rightRunMatchesOriginalGif']=all(np.array_equal(np.array(allframes[1][i]),np.array(source_run[i])) for i in range(8))
checks['leftRunIsExactMirror']=all(np.array_equal(np.array(allframes[2][i]),np.array(ImageOps.mirror(allframes[1][i]))) for i in range(8))
for r,count in enumerate(COUNTS+[8,8]):
    hashes=[]
    for c in range(8):
        f=decoded.crop((c*192,r*208,(c+1)*192,(r+1)*208)); box=f.getbbox()
        if c>=count: checks['unusedCellsTransparent'] &= box is None
        else:
            checks['allRequiredFramesPresent'] &= box is not None
            checks['safeMargins'] &= box is not None and box[0]>=4 and box[1]>=4 and box[2]<=188 and box[3]<=204
            hashes.append(hashlib.sha256(f.tobytes()).hexdigest())
            report['frames'].append({'row':r,'column':c,'bbox':box})
    checks[f'row{r}HasDistinctFrames']=len(set(hashes))>1
assert all(checks.values()),checks
report['status']='passed structural validation; visual review required; native app playback not asserted'
(ROOT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'method':'source-pixel','atlas':list(atlas.size),'frames':report['expectedFrames']},indent=2))
