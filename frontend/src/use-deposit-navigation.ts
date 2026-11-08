import { useEffect, useRef, useState } from 'react';

const key='haFinanceDeposit';
function currentDeposit():string|undefined{
 const entry=window.history.state?.[key];
 return entry?.path===location.pathname && typeof entry.id==='string'?entry.id:undefined;
}

/** Keep detail navigation in browser history for system Back and edge swipes. */
export function useDepositNavigation(blocked:boolean){
 const [selected,setSelected]=useState<string|undefined>(currentDeposit);
 const surface=useRef<HTMLElement>(null);
 useEffect(()=>{
  const pop=()=>setSelected(currentDeposit());
  window.addEventListener('popstate',pop);
  return ()=>window.removeEventListener('popstate',pop);
 },[]);
 function navigate(id:string|undefined){
  if(id===selected)return;
  if(id){
   window.history.pushState({...window.history.state,[key]:{id,path:location.pathname}},'');
   setSelected(id);
  }else if(currentDeposit()){
   window.history.back();
  }else setSelected(undefined);
 }
 useEffect(()=>{
  const element=surface.current;
  if(!element||!selected||blocked)return;
  let start:{x:number;y:number}|undefined;
  const begin=(e:TouchEvent)=>{
   if(e.touches.length!==1){start=undefined;return}
   const touch=e.touches[0];
   const edge=element.getBoundingClientRect().left;
   start=touch.clientX-edge<=32?{x:touch.clientX,y:touch.clientY}:undefined;
  };
  const move=(e:TouchEvent)=>{
   if(!start||e.touches.length!==1){start=undefined;return}
   const dx=e.touches[0].clientX-start.x,dy=Math.abs(e.touches[0].clientY-start.y);
   if(dy>30||dx< -10){start=undefined;return}
   if(dx>16&&dx>dy*2&&e.cancelable)e.preventDefault();
  };
  const end=(e:TouchEvent)=>{
   if(!start)return;
   const origin=start;start=undefined;
   const touch=e.changedTouches[0];
   if(touch&&touch.clientX-origin.x>=80&&Math.abs(touch.clientY-origin.y)<30)navigate(undefined);
  };
  const cancel=()=>{start=undefined};
  element.addEventListener('touchstart',begin,{passive:true});
  element.addEventListener('touchmove',move,{passive:false});
  element.addEventListener('touchend',end);
  element.addEventListener('touchcancel',cancel);
  return ()=>{
   element.removeEventListener('touchstart',begin);element.removeEventListener('touchmove',move);
   element.removeEventListener('touchend',end);element.removeEventListener('touchcancel',cancel);
  };
 },[selected,blocked]);
 return {selected,navigate,surface};
}
