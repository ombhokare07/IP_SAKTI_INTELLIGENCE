'use client';
import VoiceInput from './VoiceInput';
export default function ChatBox({value,onChange,language}:{value:string,onChange:(v:string)=>void,language:string}) {return <div className="chat-compose"><label htmlFor="question">Your research question</label><textarea id="question" rows={6} required value={value} onChange={e=>onChange(e.target.value)} placeholder="Describe your invention or ask a question about IP, AYUSH, traditional knowledge or regulation…"/><VoiceInput language={language} onTranscript={onChange}/></div>;}
