import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ActionSheet, Pencil } from './action-sheet';

export function HoldCard({name,className,children,open,edit,remove,onHold}:{name:string;className:string;children:ReactNode;open:()=>void;edit?:()=>void;remove?:()=>void;onHold?:()=>void}){
 const [actions,setActions]=useState(false);
 const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
 const origin=useRef<{x:number;y:number}|undefined>(undefined);
 const held=useRef(false);
 const showActions=()=>{if(onHold)onHold();else setActions(true)};
 const cancel=()=>{clearTimeout(timer.current);timer.current=undefined};
 useEffect(()=>()=>clearTimeout(timer.current),[]);
 return <div className="hold-card-container"><button className={`${className} hold-card`} aria-label={name} onPointerDown={event=>{
  held.current=false;
  if(!event.isPrimary||event.button!==0||event.pointerType==='mouse')return;
  cancel();held.current=false;origin.current={x:event.clientX,y:event.clientY};
  timer.current=setTimeout(()=>{held.current=true;showActions()},600);
 }} onPointerMove={event=>{if(origin.current&&Math.hypot(event.clientX-origin.current.x,event.clientY-origin.current.y)>10)cancel()}}
 onPointerUp={cancel} onPointerCancel={cancel} onPointerLeave={cancel}
 onContextMenu={event=>{event.preventDefault();cancel();held.current=true;showActions()}}
 onKeyDown={event=>{if(event.key==='F10'&&event.shiftKey){event.preventDefault();showActions()}}}
 onClick={()=>{if(held.current){held.current=false;return}if(!actions)open()}}>{children}</button>
 <button className="desktop-card-actions icon-button" aria-label={`Действия: ${name}`} onClick={showActions}><Pencil/></button>
 {actions&&<ActionSheet title={name} close={()=>setActions(false)} actions={[
  ...(edit?[{label:'Изменить',run:edit}]:[]),...(remove?[{label:'Удалить',danger:true,run:remove}]:[]),{label:'Отмена',run:()=>setActions(false)},
 ]}/>}
 </div>
}
