class ErrorNegocio(Exception):
    def __init__(self, codigo: str, mensaje: str, estado_http: int = 422, pasos=()):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.estado_http = estado_http
        self.pasos = tuple(pasos)
