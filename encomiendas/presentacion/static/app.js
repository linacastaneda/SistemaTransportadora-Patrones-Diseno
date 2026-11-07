'use strict';

document.querySelectorAll('[data-print]').forEach(button => {
  button.addEventListener('click', () => window.print());
});

const source = document.getElementById('ventas-datos');
const select = document.getElementById('venta_id');
if (source && select) {
  const ventas = JSON.parse(source.textContent);
  select.addEventListener('change', () => {
    const venta = ventas.find(item => String(item.id) === select.value);
    if (!venta) return;
    const campos = ['origen_id', 'destino_id', 'remitente_nombre', 'remitente_documento',
      'remitente_telefono', 'destinatario_nombre', 'destinatario_documento',
      'destinatario_telefono', 'direccion_entrega'
    ];
    campos.forEach(nombre => {
      const input = document.getElementById(nombre);
      if (input) input.value = venta[nombre];
    });
    document.getElementById('viaje_id').value = '';
  });
}
