const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const path = require('path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'preview.html'), 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(source);
let raf;
let time = 0;
const nodes = new Map();
function node(tag) {
  return {tag, children: [], attrs: {}, textContent: '', width: 192, height: 208,
    append(...els) { this.children.push(...els); },
    setAttribute(k,v) { this.attrs[k] = v; },
    getBoundingClientRect() { return {left:0,top:0,width:192,height:208}; },
    getContext() { return {clearRect(){},drawImage(image,x,y,w,h) {
      assert(x>=0 && x+w<=1536, 'frame extends horizontally beyond atlas');
      assert(y>=0 && y+h<=2288, 'frame extends vertically beyond atlas');
      assert.equal(w,192); assert.equal(h,208);
    }}; }
  };
}
const ctx={Image:class {constructor(){this.complete=true;this.naturalWidth=1536;}},
  document:{getElementById(id){if(!nodes.has(id))nodes.set(id,node('div'));return nodes.get(id);},createElement:node,body:{classList:{toggle(){return true;}}}},
  performance:{now:()=>time},matchMedia:()=>({matches:false}),requestAnimationFrame:f=>raf=f,console};
vm.createContext(ctx);vm.runInContext(source,ctx);
assert.equal(nodes.get('actions').children.length,9);
assert.equal(nodes.get('grid').children.length,9);
for(let row=0;row<9;row++){
  nodes.get('actions').children[row].onclick();
  for(time=0;time<9000;time+=70) raf(time);
}
nodes.get('pause').onclick(); raf(time);
nodes.get('step').onclick(); raf(time);
nodes.get('pause').onclick();
nodes.get('look').onclick();
for(let i=0;i<16;i++){
  const a=i*Math.PI/8;
  nodes.get('stage').onpointermove({clientX:96+150*Math.sin(a),clientY:104-150*Math.cos(a)});
  raf(time);
  assert.equal(nodes.get('frameCount').textContent,`观察方向 ${i*22.5}°`);
}
nodes.get('stage').onpointerleave();raf(time);
nodes.get('theme').onclick();
assert.equal(nodes.get('theme').textContent,'深色背景');
console.log('PASS: 9 states, animation frame bounds, pause/step/resume, 16 pointer directions, theme toggle. DOM/canvas stub test; not browser UI verification.');
