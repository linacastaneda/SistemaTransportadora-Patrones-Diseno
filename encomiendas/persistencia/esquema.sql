CREATE TABLE IF NOT EXISTS sucursales (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, activa INTEGER NOT NULL CHECK(activa IN (0,1))
);
CREATE TABLE IF NOT EXISTS empleados (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
 clave_hash TEXT NOT NULL, rol TEXT NOT NULL CHECK(rol IN ('operador','coordinador')),
 sucursal_id INTEGER NOT NULL REFERENCES sucursales(id), activo INTEGER NOT NULL CHECK(activo IN (0,1))
);
CREATE TABLE IF NOT EXISTS viajes (
 id INTEGER PRIMARY KEY, codigo TEXT NOT NULL UNIQUE,
 origen_id INTEGER NOT NULL REFERENCES sucursales(id), destino_id INTEGER NOT NULL REFERENCES sucursales(id),
 fecha_salida TEXT NOT NULL, placa TEXT NOT NULL,
 peso_maximo_g INTEGER NOT NULL CHECK(peso_maximo_g > 0), volumen_maximo_cm3 INTEGER NOT NULL CHECK(volumen_maximo_cm3 > 0),
 activo INTEGER NOT NULL CHECK(activo IN (0,1)), recibe_carga INTEGER NOT NULL CHECK(recibe_carga IN (0,1)),
 vehiculo_activo INTEGER NOT NULL CHECK(vehiculo_activo IN (0,1)), conductor TEXT NOT NULL, ayudante TEXT NOT NULL,
 salida_autorizada INTEGER NOT NULL CHECK(salida_autorizada IN (0,1)), llegada_registrada INTEGER NOT NULL CHECK(llegada_registrada IN (0,1)),
 CHECK(origen_id <> destino_id)
);
CREATE TABLE IF NOT EXISTS ventas (
 id INTEGER PRIMARY KEY, referencia TEXT NOT NULL UNIQUE,
 origen_id INTEGER NOT NULL REFERENCES sucursales(id), destino_id INTEGER NOT NULL REFERENCES sucursales(id),
 remitente_nombre TEXT NOT NULL, remitente_documento TEXT NOT NULL, remitente_telefono TEXT NOT NULL,
 destinatario_nombre TEXT NOT NULL, destinatario_documento TEXT NOT NULL, destinatario_telefono TEXT NOT NULL,
 direccion_entrega TEXT NOT NULL, total_centavos INTEGER NOT NULL CHECK(total_centavos > 0),
 activa INTEGER NOT NULL CHECK(activa IN (0,1))
);
CREATE TABLE IF NOT EXISTS pagos (
 id INTEGER PRIMARY KEY, referencia TEXT NOT NULL UNIQUE, venta_id INTEGER NOT NULL REFERENCES ventas(id),
 importe_centavos INTEGER NOT NULL CHECK(importe_centavos > 0), valido INTEGER NOT NULL CHECK(valido IN (0,1))
);
CREATE TABLE IF NOT EXISTS guias (
 id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT UNIQUE,
 venta_id INTEGER NOT NULL UNIQUE REFERENCES ventas(id), viaje_id INTEGER NOT NULL REFERENCES viajes(id),
 origen_id INTEGER NOT NULL REFERENCES sucursales(id), destino_id INTEGER NOT NULL REFERENCES sucursales(id),
 remitente_nombre TEXT NOT NULL, remitente_documento TEXT NOT NULL, remitente_telefono TEXT NOT NULL,
 destinatario_nombre TEXT NOT NULL, destinatario_documento TEXT NOT NULL, destinatario_telefono TEXT NOT NULL,
 direccion_entrega TEXT NOT NULL, descripcion TEXT NOT NULL,
 peso_g INTEGER NOT NULL CHECK(peso_g > 0), largo_cm INTEGER NOT NULL CHECK(largo_cm > 0),
 ancho_cm INTEGER NOT NULL CHECK(ancho_cm > 0), alto_cm INTEGER NOT NULL CHECK(alto_cm > 0),
 valor_centavos INTEGER NOT NULL CHECK(valor_centavos >= 0), observaciones TEXT NOT NULL,
 estado TEXT NOT NULL CHECK(estado IN ('RECIBIDO','EN_TRANSITO','EN_DESTINO','ENTREGADO')),
 version INTEGER NOT NULL DEFAULT 1 CHECK(version > 0), creado_por INTEGER NOT NULL REFERENCES empleados(id),
 creado_en TEXT NOT NULL, token_registro TEXT NOT NULL UNIQUE, huella TEXT NOT NULL, validaciones_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asignaciones (
 guia_id INTEGER PRIMARY KEY REFERENCES guias(id), viaje_id INTEGER NOT NULL REFERENCES viajes(id),
 peso_g INTEGER NOT NULL CHECK(peso_g > 0), volumen_cm3 INTEGER NOT NULL CHECK(volumen_cm3 > 0)
);
CREATE TABLE IF NOT EXISTS eventos (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guia_id INTEGER NOT NULL REFERENCES guias(id),
 estado_anterior TEXT, estado_nuevo TEXT NOT NULL, accion TEXT NOT NULL,
 actor_id INTEGER NOT NULL REFERENCES empleados(id), fecha TEXT NOT NULL,
 receptor_nombre TEXT NOT NULL DEFAULT '', receptor_documento TEXT NOT NULL DEFAULT '', constancia TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS movimientos_viaje (
 id INTEGER PRIMARY KEY AUTOINCREMENT, viaje_id INTEGER NOT NULL REFERENCES viajes(id),
 accion TEXT NOT NULL, actor_id INTEGER NOT NULL REFERENCES empleados(id), fecha TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guias_estado ON guias(estado, id);
CREATE INDEX IF NOT EXISTS idx_guias_sucursales ON guias(origen_id, destino_id);
CREATE INDEX IF NOT EXISTS idx_asignaciones_viaje ON asignaciones(viaje_id);
CREATE INDEX IF NOT EXISTS idx_eventos_guia ON eventos(guia_id,id);
CREATE TRIGGER IF NOT EXISTS proteger_carga BEFORE INSERT ON asignaciones BEGIN
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM guias g JOIN viajes v ON v.id=NEW.viaje_id
   WHERE g.id=NEW.guia_id AND g.viaje_id=v.id AND g.peso_g=NEW.peso_g
   AND g.largo_cm*g.ancho_cm*g.alto_cm=NEW.volumen_cm3
   AND g.origen_id=v.origen_id AND g.destino_id=v.destino_id
   AND v.activo=1 AND v.recibe_carga=1 AND v.llegada_registrada=0
   AND NEW.peso_g + COALESCE((SELECT SUM(peso_g) FROM asignaciones WHERE viaje_id=v.id),0)<=v.peso_maximo_g
   AND NEW.volumen_cm3 + COALESCE((SELECT SUM(volumen_cm3) FROM asignaciones WHERE viaje_id=v.id),0)<=v.volumen_maximo_cm3
 ) THEN RAISE(ABORT,'Asignacion invalida o capacidad insuficiente') END;
END;
CREATE TRIGGER IF NOT EXISTS asignacion_inmutable BEFORE UPDATE ON asignaciones BEGIN
 SELECT RAISE(ABORT,'La asignacion confirmada no se modifica');
END;
CREATE TRIGGER IF NOT EXISTS asignacion_no_borrar BEFORE DELETE ON asignaciones BEGIN
 SELECT RAISE(ABORT,'La asignacion confirmada conserva su historial');
END;
CREATE TRIGGER IF NOT EXISTS proteger_transicion BEFORE UPDATE OF estado ON guias
 WHEN NOT ((OLD.estado='RECIBIDO' AND NEW.estado='EN_TRANSITO')
 OR (OLD.estado='EN_TRANSITO' AND NEW.estado='EN_DESTINO')
 OR (OLD.estado='EN_DESTINO' AND NEW.estado='ENTREGADO'))
 BEGIN SELECT RAISE(ABORT,'Transicion no permitida'); END;
CREATE TRIGGER IF NOT EXISTS evento_inmutable BEFORE UPDATE ON eventos BEGIN
 SELECT RAISE(ABORT,'El historial no se modifica');
END;
CREATE TRIGGER IF NOT EXISTS evento_no_borrar BEFORE DELETE ON eventos BEGIN
 SELECT RAISE(ABORT,'El historial no se elimina');
END;
