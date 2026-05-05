function analyze(){
 fetch("/api/analyze",{
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({
    text: document.getElementById("text").value
  })
 })
 .then(r=>r.json())
 .then(d=>{
   document.getElementById("result").innerText =
     d.status + " ("+d.risk+")";
 })
}