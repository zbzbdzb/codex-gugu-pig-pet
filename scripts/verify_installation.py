"""Exercise the Windows installer in isolated directories, never the real pet."""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[1]
TEST=ROOT/'.test-output'/('installation-'+uuid.uuid4().hex)
TEST.mkdir(parents=True)
HOME=TEST/'codex-data'
INSTALL=ROOT/'install.ps1'
FILES=('pet.json','spritesheet.webp')
RESULTS={}

def run(*args,success=True):
    proc=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass',
                         '-File',str(INSTALL),'-CodexHome',str(HOME),*args],
                        capture_output=True,text=True)
    assert (proc.returncode==0)==success, proc.stdout+proc.stderr
    return proc

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def matches(a,b):
    return all(digest(a/f)==digest(b/f) for f in FILES)

def record(name):
    RESULTS[name]=True
    print('PASS:',name)

target=HOME/'pets/gugu-pig'
source=ROOT/'dist/gugu-pig'
run('-DryRun')
assert not HOME.exists()
record('dryRunDoesNotWrite')
run()
assert matches(source,target)
record('freshInstallMatchesPackage')
run()
assert matches(source,target) and not (HOME/'pet-backups').exists()
record('repeatInstallIsIdempotent')

# Simulate an older package while keeping its manifest identity valid.
old_sprite=(target/'spritesheet.webp').read_bytes()+b'old-package-marker'
(target/'spritesheet.webp').write_bytes(old_sprite)
run(success=False)
assert (target/'spritesheet.webp').read_bytes()==old_sprite
record('differentPackageRequiresUpdate')
run('-Update','-DryRun')
assert (target/'spritesheet.webp').read_bytes()==old_sprite
assert not (HOME/'pet-backups').exists()
record('updateDryRunPreservesInstalledFiles')
run('-Update')
assert matches(source,target)
backups=list((HOME/'pet-backups/gugu-pig').iterdir())
assert len(backups)==1
assert (backups[0]/'spritesheet.webp').read_bytes()==old_sprite
assert (backups[0]/'pet.json').read_bytes()==(source/'pet.json').read_bytes()
record('updateBacksUpExactPreviousPackage')

bad=json.loads((target/'pet.json').read_text(encoding='utf8'))
bad['id']='different-pet'
(target/'pet.json').write_text(json.dumps(bad),encoding='utf8')
before={f:digest(target/f) for f in FILES}
run('-Update',success=False)
assert before=={f:digest(target/f) for f in FILES}
record('differentPetIdentityIsNeverOverwritten')

run('-Legacy')
assert matches(ROOT/'dist/gugu-pig-v1',HOME/'pets/gugu-pig-v1')
record('legacyInstallMatchesPackage')
(ROOT/'validation-installation.json').write_text(
    json.dumps({'platform':'Windows','checks':RESULTS},indent=2)+'\n',encoding='utf8')
