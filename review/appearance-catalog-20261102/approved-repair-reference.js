/* Apply after coloredHairSource and registered 941x1672 placement. No fixed pigment.
   Mapping entries: [destination pixel index, donor pixel index, coverage, donor alpha].
   Donor RGB always comes from the CURRENT selected hair color, before patching.
   Local maps are keyed by face ID and hair ID; excluded styles stay excluded. */
function applyRegisteredHairRepair(input, mapping) {
  if (input.width !== 941 || input.height !== 1672) throw new Error('Expected registered 941x1672 hair');
  const source = input.getContext('2d').getImageData(0,0,941,1672);
  const output = new ImageData(new Uint8ClampedArray(source.data),941,1672);
  for (const [destination,donor,coverage,alpha] of mapping) {
    const q=destination*4,k=donor*4;
    for(let c=0;c<3;c++) output.data[q+c]=Math.round(source.data[k+c]*coverage+source.data[q+c]*(1-coverage));
    output.data[q+3]=Math.round(alpha*coverage+source.data[q+3]*(1-coverage));
  }
  const result=document.createElement('canvas'); result.width=941; result.height=1672;
  result.getContext('2d').putImageData(output,0,0); result.repairImageData=output; return result;
}
