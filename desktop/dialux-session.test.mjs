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
