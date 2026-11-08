import type { Deposit } from './types';
export const money = (n:number) => new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:2}).format(n/100);
export const kopecks = (s:string) => {const n=Number(s.replace(',','.')); if(!Number.isFinite(n)||n<0) throw Error('Введите положительную сумму'); return Math.round(n*100)};
export const total = (d:Deposit) => {const actual=d.expenses.filter(e=>e.paid).reduce((s,e)=>s+e.amount,0);const expected=d.expenses.filter(e=>!e.paid).reduce((s,e)=>s+e.amount,0);return {actual,expected,balance:d.principal-actual,available:d.principal-actual-expected}};
export const today = () => new Date().toLocaleDateString('sv-SE');
