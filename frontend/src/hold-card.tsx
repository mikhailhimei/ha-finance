import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ActionSheet } from './action-sheet';

export function HoldCard({name,className,children,open,edit,remove}:{name:string;className:string;children:ReactNode;open:()=>void;edit:()=>void;remove:()=>void}){
 const [actions,setActions]=useState(false);
 const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
 const origin=useRef<{x:number;y:number}|undefined>(undefined);
 const held=useRef(false);
 const cancel=()=>{clearTimeout(timer.current);timer.current=undefined};
 useEffect(()=>()=>clearTimeout(timer.current),[]);
 return <><button className={`${className} hold-card`} aria-label={name} onPointerDown={event=>{
  if(!event.isPrimary||event.button!==0)return;
  cancel();held.current=false;origin.current={x:event.clientX,y:event.clientY};
  timer.current=setTimeout(()=>{held.current=true;setActions(true)},600);
 }} onPointerMove={event=>{if(origin.current&&Math.hypot(event.clientX-origin.current.x,event.clientY-origin.current.y)>10)cancel()}}
 onPointerUp={cancel} onPointerCancel={cancel} onPointerLeave={cancel}
 onContextMenu={event=>{event.preventDefault();cancel();held.current=true;setActions(true)}}
 onKeyDown={event=>{if(event.key==='F10'&&event.shiftKey){event.preventDefault();setActions(true)}}}
 onClick={()=>{if(held.current){held.current=false;return}if(!actions)open()}}>{children}</button>
 {actions&&<ActionSheet title={name} close={()=>setActions(false)} actions={[
  {label:'Изменить',run:edit},{label:'Удалить',danger:true,run:remove},{label:'Отмена',run:()=>setActions(false)},
 ]}/>}
 </>
}
