import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DialuxSession} from './dialux-session.mjs';

function fixture(extra = '') {
  const window = {id: 1, app: 'process:C:\\DIALux\\DIALux_x64.exe'};
  const calls=[];
  const sky={list_windows:async()=>[window],get_window:async()=>window,activate_window:async()=>{},
    get_window_state:async()=>({window,accessibility:{tree:
      '\t0 window DIALux\n\t\t1 button Save ID: Save\n\t\t2 button Calculate ID: CalculationButtonStart'+extra}}),
    click:async x=>calls.push(x),press_key:async x=>calls.push(x)};
  return {sky,calls,session:new DialuxSession(sky)};
}

test('uses fresh observed control and invalidates consumed state',async()=>{
  const f=fixture(), state=await f.session.connect();
  await f.session.save(state);
  assert.equal(f.calls[0].key,'Control_L+s');
  await assert.rejects(f.session.calculate(state),/Stale/);
  assert.equal(f.calls.length,1);
});
test('does not select duplicate or foreign controls',async()=>{
  const f=fixture('\n\t\t3 window Foreign\n\t\t\t4 button Save ID: Save');
  await f.session.save(await f.session.connect());
  assert.equal(f.calls[0].key,'Control_L+s');
  const g=fixture('\n\t\t4 button Save ID: Save');
  await assert.rejects(g.session.save(await g.session.connect()),/one enabled/);
  assert.equal(g.calls.length,0);
});
test('ambiguous target refuses activation',async()=>{
  const f=fixture(); f.sky.list_windows=async()=>[
    {id:1,app:'C:\\DIALux_x64.exe'},{id:2,app:'C:\\DIALux_x64.exe'}];
  await assert.rejects(f.session.connect(),/found 2/);
});
test('failed click cannot be blindly repeated',async()=>{
  const f=fixture();f.sky.press_key=async()=>{throw Error('input outcome unknown')};
  const s=await f.session.connect();
  await assert.rejects(f.session.save(s),/unknown/);
  await assert.rejects(f.session.save(s),/Stale/);
});

test('visual fallback binds coordinates to current screenshot, not stale accessibility',async()=>{
  const f=fixture();
  const read=f.sky.get_window_state;
  f.sky.get_window_state=async()=>({...await read(),screenshots:[{id:'current',width:800,height:600}]});
  const s=await f.session.connect();
  await f.session.clickObserved(s,{action:'save',screenshotId:'current',x:100,y:70});
  assert.deepEqual(f.calls[0],{window:s.window,screenshotId:'current',x:100,y:70});
  await assert.rejects(f.session.clickObserved(s,{action:'save',screenshotId:'current',x:100,y:70}),/Stale/);
  for(const args of [
    {action:'delete',screenshotId:'current',x:1,y:1},
    {action:'save',screenshotId:'old',x:1,y:1},
    {action:'save',screenshotId:'current',x:800,y:1},
    {action:'save',screenshotId:'current',x:NaN,y:1},
  ]) await assert.rejects(f.session.clickObserved(await f.session.observe(),args));
  assert.equal(f.calls.length,1);
});

test('capture redirected to another window invalidates the session observation',async()=>{
  const f=fixture(); const s=await f.session.connect();
  f.sky.get_window_state=async()=>({window:{id:2,app:'other.exe'}});
  await assert.rejects(f.session.observe(),/differs/);
  await assert.rejects(f.session.save(s),/Stale/);
  assert.equal(f.calls.length,0);
});

test('DIALux window-role message boxes block accessibility actions',async()=>{
  const f=fixture('\n\t\t3 window DIALux ID: InformationBox\n\t\t\t4 button Yes ID: Yes');
  await assert.rejects(f.session.calculate(await f.session.connect()),/message box/);
  assert.equal(f.calls.length,0);
});

test('calculate accepts an explicitly inspected screenshot point',async()=>{
  const f=fixture(), read=f.sky.get_window_state;
  f.sky.get_window_state=async()=>({...await read(),screenshots:[{id:'shot',width:800,height:600}]});
  await f.session.calculate(await f.session.connect(),{screenshotId:'shot',x:650,y:70});
  assert.equal(f.calls[0].screenshotId,'shot');
  assert.equal(f.calls[0].element_index,undefined);
});
