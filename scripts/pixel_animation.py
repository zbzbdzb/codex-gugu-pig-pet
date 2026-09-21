"""Source-pixel animation, explicitly requested by the user.

Each pose reuses one 40x35 master; no generated drawings are consumed.
The original eyes, nose, ear and tail are reused; the interaction pose moves
only the ear tip and blinks both eyes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import json, math

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Image.open(ROOT/'sources/像素猪.gif').convert('RGBA')
ORIGINAL = SOURCE.resize((40,35), Image.Resampling.NEAREST)
# Confirm this is a lossless pixel-grid extraction, not a redrawing.
assert np.array_equal(np.array(ORIGINAL.resize(SOURCE.size, Image.Resampling.NEAREST)), np.array(SOURCE))
BODY=(254,210,176,255)
BLACK=(0,0,0,255)
DARK=(54,42,40,255)
CLEAR=(0,0,0,0)
BASE=ORIGINAL.copy()
# Lower only the highest source contour pixels by one source pixel. Retain
# several shallow steps between shoulder, back and rump instead of a long cut.
BACK_TOP={9:8,10:8,11:8,12:7,13:7,14:7,15:6,16:6,17:6,
          18:6,19:6,20:6,21:7,22:7,23:7,24:7,25:7,26:8,27:8}
for x,top in BACK_TOP.items():
    for y in range(4,top): BASE.putpixel((x,y),CLEAR)
    BASE.putpixel((x,top),BLACK)
# A shallow haunch followed by a small inset at the hind leg replaces the
# uninterrupted diagonal. Confine all edits to the rear edge, x=6..11/y=18..25.
REAR_EDGE={18:6,19:6,20:7,21:7,22:8,23:9,24:11,25:11}
for y,left in REAR_EDGE.items():
    for x in range(6,12):
        BASE.putpixel((x,y),CLEAR if x<left else BLACK if x==left else BODY)
BASE.putpixel((10,23),BLACK)
EYES=((22,16),(29,15))
NOSE=(25,18,32,22)
TAIL=(3,7,9,13)
EAR=(17,11,22,17)
LEGS=(10,24,30,30)
checks={}
for label,box in [('nose',NOSE),('tail',TAIL),('ear',EAR),('frontAndMiddleLegs',(17,24,30,30))]:
    checks[label+'MasterMatchesSource']=np.array_equal(np.array(BASE.crop(box)),np.array(ORIGINAL.crop(box)))

def eyes(im, mode='open', offset=(0,0)):
    dr=ImageDraw.Draw(im)
    for x,y in EYES:
        dr.rectangle((x,y,x+1,y+1),fill=BODY)
        x+=offset[0]; y+=offset[1]
        if mode=='open': dr.rectangle((x,y,x+1,y+1),fill=DARK)
        elif mode=='happy':
            # A complete, symmetric three-pixel arch instead of two diagonal
            # dots. Both eyes use the same shape at their original heights.
            dr.point((x,y+1),fill=DARK)
            dr.point((x+1,y),fill=DARK)
            dr.point((x+2,y+1),fill=DARK)
        else: dr.line((x,y+1,x+1,y+1),fill=DARK)

def lift_foreleg(im, amount):
    if not amount: return
    part=im.crop((24,26,30,30))
    ImageDraw.Draw(im).rectangle((24,26,29,29),fill=CLEAR)
    im.alpha_composite(part,(24,26-amount))

def twitch_ear(im,phase):
    # Reuse the source ear colors and outline, moving its upper tip at most
    # one source pixel. The pig's silhouette and all three legs stay planted.
    if phase not in (1,2): return
    ImageDraw.Draw(im).rectangle((17,11,21,16),fill=BODY)
    for y in range(11,17):
        for x in range(17,22):
            color=ORIGINAL.getpixel((x,y))
            if color==BODY: continue
            dx=-1 if x>=20 and y<=14 else 0
            dy=1 if phase==2 and x>=20 and y<=12 else 0
            im.putpixel((x+dx,y+dy),color)

def tuck_legs(im):
    # Shorten the existing three legs by two grid rows. Reuse their original
    # tapered sides, sole pixels and coral forehoof; do not replace the belly
    # with a horizontal line or erase the feet.
    lower=im.copy()
    ImageDraw.Draw(im).rectangle((9,24,32,30),fill=CLEAR)
    for target,source in [(24,24),(25,26),(26,28),(27,29)]:
        im.paste(lower.crop((9,source,33,source+1)),(9,target))

def prop(im,kind,tap=0):
    dr=ImageDraw.Draw(im)
    if kind=='laptop':
        dr.rectangle((29,25,37,30),fill=BLACK)
        dr.rectangle((30,26,36,29),fill='#15394F')
        dr.rectangle((33,27,34,28),fill='#43BED6')
        dr.rectangle((25,31,37,31),fill=BLACK)
        dr.line((26,30,28,30),fill='#456579')
    else:
        dr.rectangle((31,23,36,31),fill=BLACK)
        dr.rectangle((32,24,35,30),fill='#FFF2D4')
        for y in (25,27,29): dr.line((33,y,34,y),fill=DARK)

def tears(im,phase):
    dr=ImageDraw.Draw(im)
    # Route the right tear beside the snout, never through its protected pixels.
    dr.line((22,18,22,23+phase%2),fill='#69BDEB')
    dr.line([(29,17),(31,17),(32,18),(33,19),(33,24+phase%2)],fill='#69BDEB')
    if phase%3:
        dr.point((22,25+phase%2),fill='#69BDEB')
        dr.point((33,26+phase%2),fill='#69BDEB')

def render(im,baseline=174,dy=0):
    # One shared nearest-neighbour scale, with a fixed source-grid origin.
    sprite=im.resize((180,158),Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(192,208))
    frame.alpha_composite(sprite,(6,round(baseline-135+dy)))
    return frame

def sleep_marks(frame,phase):
    # Compact pixel z's rise toward the upper right, outside the silhouette.
    dr=ImageDraw.Draw(frame)
    drift=[0,-1,-2,-3,-2,-1][phase]
    glyph=('11111','00010','00100','01000','11111')
    for x,y,scale in [(143,64,1),(153,50,2),(169,30,3)]:
        for row,line in enumerate(glyph):
            for col,pixel in enumerate(line):
                if pixel=='1':
                    left=x+col*scale; top=y+drift+row*scale
                    dr.rectangle((left,top,left+scale-1,top+scale-1),fill='#8DABD9')

def waiting_marks(frame,phase):
    # A fixed speech bubble with sequential dots makes the waiting state
    # legible even when the body is still. Keep it clear of the ears and back.
    dr=ImageDraw.Draw(frame)
    dr.rectangle((132,34,180,57),fill=BLACK)
    dr.rectangle((135,37,177,54),fill='#FFF2D4')
    dr.polygon([(142,56),(148,56),(142,63)],fill=BLACK)
    dr.polygon([(143,54),(146,54),(143,58)],fill='#FFF2D4')
    for n in range([1,1,2,2,3,3][phase]):
        x=142+n*12
        dr.rectangle((x,44,x+4,48),fill=DARK)

def build():
    states={}; low={}
    for state,count in [(0,6),(3,4),(4,5),(5,8),(6,6),(7,6),(8,6)]:
        fs=[]; ps=[]
        for c in range(count):
            im=BASE.copy(); baseline=174; dy=0
            if state==0:
                eyes(im,'closed')
                tuck_legs(im)
                dy=9+[0,0,-1,-1,0,0][c]
            elif state==3:
                twitch_ear(im,c)
                eyes(im,['open','open','closed','open'][c])
            elif state==4:
                eyes(im,['closed','happy','happy','open','closed'][c])
                baseline=[177,151,125,150,176][c]
            elif state==5:
                eyes(im,['open','open','half','closed','closed','half','open','open'][c])
                tears(im,c)
            elif state==6:
                eyes(im,['open','open','half','closed','open','open'][c])
            elif state==7:
                eyes(im,['open','open','half','closed','open','open'][c])
                lift_foreleg(im,[0,1,0,1,0,1][c]); prop(im,'laptop')
            elif state==8:
                eyes(im,['open','open','half','closed','half','open'][c]); prop(im,'paper')
            assert np.array_equal(np.array(im.crop(NOSE)),np.array(ORIGINAL.crop(NOSE))),(state,c,'nose')
            assert np.array_equal(np.array(im.crop(TAIL)),np.array(ORIGINAL.crop(TAIL))),(state,c,'tail')
            if state!=3:
                assert np.array_equal(np.array(im.crop(EAR)),np.array(ORIGINAL.crop(EAR))),(state,c,'ear')
            ps.append(im)
            frame=render(im,baseline,dy)
            if state==0: sleep_marks(frame,c)
            elif state==6: waiting_marks(frame,c)
            fs.append(frame)
        states[state]=fs; low[state]=ps
    looks=[]
    for n in range(16):
        angle=n*math.pi/8
        im=BASE.copy()
        dx=round(abs(math.sin(angle))); dy=round(-math.cos(angle))
        eyes(im,'open',(dx,dy))
        assert np.array_equal(np.array(im.crop(NOSE)),np.array(ORIGINAL.crop(NOSE)))
        if n>8: im=ImageOps.mirror(im)
        looks.append(render(im))
    checks['all57EditedPosesKeepOriginalNoseAndTail']=True
    checks['earPreservedExceptIntentionalTwitch']=True
    checks['eyeSizeIsOriginal2x2']=all(np.all(np.array(ORIGINAL.crop((x,y,x+2,y+2)))==DARK) for x,y in EYES)
    checks['noGeneratedSpritesConsumed']=True
    # In review, only the two eye rectangles can change across frames.
    first=np.array(low[8][0]); allowed=np.zeros((35,40),bool)
    for x,y in EYES: allowed[y:y+2,x:x+2]=True
    checks['reviewChangesOnlyBothEyeRegions']=all(not np.any(np.any(np.array(p)!=first,axis=2)&~allowed) for p in low[8])
    checks['stationaryLegsMatchMaster']=all(np.array_equal(np.array(p.crop(LEGS)),np.array(BASE.crop(LEGS))) for s in (3,4,6) for p in low[s])
    assert all(checks.values()),checks
    (ROOT/'validation-pixels.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    BASE.save(ROOT/'previews/pixel-master.png')
    return states,looks
