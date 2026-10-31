const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const scenario = process.argv[2];
const elements = new Map(), requests = [], timers = [];
const stored = new Map(scenario==='cached_name'?[['spotter.runnerName','Andrew']]:[]);
function element(id='') {
  return {id, hidden:false, style:{}, textContent:'', value:'', options:[], children:[],
    listeners:{}, addEventListener(kind,fn){this.listeners[kind]=fn;},
    dispatchEvent(event){this.listeners[event.type]?.(event);}, setAttribute(){},
    replaceChildren(...children){this.children=children; this.options=children;},
    after(child){elements.set(child.id,child);}};
}
function get(id) {if(!elements.has(id))elements.set(id,element(id));return elements.get(id);}
get('provider').options=[{value:'spotter'},{value:'dream'}];
get('quickRun').textContent=scenario==='ended'?'Run':'Stop run';
get('status').textContent=scenario==='ended'?'Stopped':'Running';
const state={attempt_id:'confirmed-attempt',provider:scenario==='ended'?null:{provider:'spotter'},
  runner_name:['cached_name','new_visitor'].includes(scenario)?null:'Andrew',
  run_configuration:{provider:'spotter'},
  status:scenario==='ended'?'safety_aborted':'running',conversation_sharing:{enabled:false},
  interactions:{events:[{kind:'model_request',message:'PRIVATE WIRE PAYLOAD'},
    {kind:'model_progress',message:'Spotter screen · The orange block remains on the table.',
      details:{spotter_phase:'screen',progress_type:'status'}}]}};
const sandbox={window:{},document:{getElementById:get,createElement:()=>element()},
  MutationObserver:class{observe(){}},Event:class{constructor(type){this.type=type;}},setInterval(fn){timers.push(fn);},
  localStorage:{getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value),removeItem:key=>stored.delete(key)},
  fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>state};}};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[3],'utf8'),sandbox);
(async()=>{
 await sandbox.window.yamApplication.sessionReady({robot_id:'robohouse',spotter:{
   base_provider:scenario==='yam1'?'dreamzero':'dream',stations:[],configured:true,
   base:'Dream-1',supervisor:'Qwen',dream_runtime:{ready:true}}});
 if(scenario==='yam1'){
   assert.equal(requests.length,0);assert.equal(elements.has('spotterOwnActivity'),false);
 } else {
   const name=get('runnerName');
   assert.equal(name.value,scenario==='new_visitor'?'':'Andrew','Known name must be restored without assigning Andrew to strangers');
   if(scenario==='running'){
     name.value='Andrew edited';name.dispatchEvent({type:'input'});
     assert.equal(stored.get('spotter.runnerName'),'Andrew edited');
     await timers.at(-1)();assert.equal(name.value,'Andrew edited','Status refresh must not overwrite a user edit');
   }
   const panel=elements.get('spotterOwnActivity');assert.ok(panel,'Runner must see owned Spotter activity');
   assert.equal(panel.hidden,false);
   const text=panel.children.map(x=>x.textContent).join('\n');
   assert.match(text,/The orange block remains on the table/);
   assert.match(text,scenario==='ended'?/Last Spotter run.*Stopped/:/Spotter activity/);
   assert.doesNotMatch(text,/PRIVATE WIRE PAYLOAD/);
   assert.equal(state.conversation_sharing.enabled,false);
   assert.deepEqual(requests.map(x=>x.url),scenario==='running'?['/api/status','/api/status']:['/api/status']);
   assert.ok(requests.every(x=>!x.options.method||x.options.method==='GET'));
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
