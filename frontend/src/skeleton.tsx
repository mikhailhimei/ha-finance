type Variant='cards'|'payments'|'preview'|'periods'|'overview';
const Line=({wide=false}:{wide?:boolean})=><span className={`skeleton-line ${wide?'wide':''}`}/>;
export function Skeleton({variant='cards',count=2}:{variant?:Variant;count?:number}){
 return <div className={`skeleton skeleton-${variant}`} role="status" aria-label="Загрузка данных" aria-busy="true"><div aria-hidden="true" className="skeleton-layout">
  {variant==='overview'?<><div className="skeleton-donut"/><div className="skeleton-metrics">{Array.from({length:3},(_,i)=><div key={i}><Line/><Line wide/></div>)}</div></>:Array.from({length:count},(_,i)=><div className="skeleton-block" key={i}><Line/><Line wide/>{variant!=='preview'&&variant!=='periods'&&<><Line/><Line wide/></>}</div>)}
 </div></div>
}
