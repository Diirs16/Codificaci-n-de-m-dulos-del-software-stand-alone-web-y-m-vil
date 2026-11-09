import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle, Send } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { enviarMensajeContacto, enviarSolicitudAdopcion } from "../services/api";
import { MENSAJE_MAX, MENSAJE_MIN, validarMensaje, validarTelefono } from "../utils/solicitud";

// Correo de atención de la política de datos (D.1). Si cambia, cambiarlo también en
// AvisoDemo.jsx, Contact.jsx, PoliticaDatos.jsx, CasillaAutorizacion.jsx, LoginModal.jsx,
// el móvil y el borrador .md.
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

const CAMPO =
  "w-full px-3 py-2.5 border border-gray-300 rounded-lg text-base bg-white focus:outline-2 focus:outline-offset-1 focus:outline-black aria-invalid:border-red-600";
const BOTON_PRINCIPAL =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-black px-5 py-2.5 font-medium text-white hover:bg-gray-800 disabled:cursor-wait disabled:bg-gray-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black";
const BOTON_SECUNDARIO =
  "inline-flex min-h-11 items-center justify-center rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium hover:bg-gray-100 disabled:cursor-wait disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black";

/**
 * Formulario real de solicitud de adopción o de mensaje de contacto (ítem 3.6, A-21).
 * Decisiones del dueño (07/11/2026): solo con sesión (el nombre y el correo salen de la
 * cuenta y no se piden), teléfono opcional solo en adopción y SIN casilla aparte: el
 * aviso B.5 informa la finalidad y vale la autorización de la cuenta con la política 1.1.
 * Dice "enviada" solo cuando la API respondió 201.
 *
 * Props: tipo ("adopcion" | "contacto"), mascota ({ id, name }, solo adopción) y
 * onCerrar (opcional: muestra el botón "Cerrar").
 */
export default function FormularioSolicitud({ tipo, mascota, onCerrar }) {
  const { user, cerrarSesionLocal, openLogin, openRegister } = useAuth();
  const esAdopcion = tipo === "adopcion";
  const id = (campo) => `${tipo}-${campo}`;

  // Lo escrito se conserva aunque haya que volver a iniciar sesión.
  const [mensaje, setMensaje] = useState("");
  const [telefono, setTelefono] = useState("");
  const [estado, setEstado] = useState("editando"); // "editando" | "enviando" | "enviada"
  const [error, setError] = useState("");
  const [campoConError, setCampoConError] = useState(null); // "mensaje" | "telefono" | null
  const [volverAEntrar, setVolverAEntrar] = useState(false); // 401 o 403 de autorización
  const [numero, setNumero] = useState(null);

  const mensajeRef = useRef(null);
  const telefonoRef = useRef(null);
  const enviadaRef = useRef(null);
  const errorRef = useRef(null);
  const [enfocarError, setEnfocarError] = useState(0); // al sumar 1, el foco va al error de la API

  useEffect(() => {
    if (estado === "enviada") enviadaRef.current?.focus();
  }, [estado]);

  // Si la API rechaza el envío, el aviso puede quedar fuera de la pantalla del celular
  useEffect(() => {
    if (enfocarError) errorRef.current?.focus();
  }, [enfocarError]);

  async function enviar(e) {
    e.preventDefault();
    if (estado === "enviando") return;
    setError("");
    setVolverAEntrar(false);

    // Primero en el navegador: así no se llama a la API con algo que va a rechazar.
    const errorMensaje = validarMensaje(mensaje);
    const errorTelefono = esAdopcion ? validarTelefono(telefono) : null;
    if (errorMensaje || errorTelefono) {
      setError(errorMensaje || errorTelefono);
      setCampoConError(errorMensaje ? "mensaje" : "telefono");
      (errorMensaje ? mensajeRef : telefonoRef).current?.focus();
      return;
    }
    setCampoConError(null);

    setEstado("enviando");
    try {
      const respuesta = esAdopcion
        ? await enviarSolicitudAdopcion(mascota.id, mensaje.trim(), telefono.trim())
        : await enviarMensajeContacto(mensaje.trim());
      setNumero(respuesta?.id ?? null);
      setEstado("enviada");
    } catch (err) {
      setEstado("editando");
      if (err.status === 401) {
        setError("Tu sesión venció. Vuelve a iniciar sesión para enviar: lo que escribiste no se pierde.");
        setVolverAEntrar(true);
      } else if (err.requiereAutorizacion) {
        setError(err.message);
        setVolverAEntrar(true);
      } else {
        setError(err.message || "No pudimos enviar. Inténtalo de nuevo en unos minutos.");
      }
      setEnfocarError((n) => n + 1);
    }
  }

  function volverAIniciarSesion() {
    setError("");
    setVolverAEntrar(false);
    // Ítem 4.13: la API ya respondió 401 (el token no vale), así que no se le pide
    // cerrar la sesión: solo se borra la de este navegador.
    cerrarSesionLocal();
    openLogin();
  }

  // --- Sin sesión: no se muestra el formulario (no se recoge nada sin cuenta) ---
  if (!user) {
    return (
      <div className="space-y-3 rounded-lg border border-gray-200 p-4">
        <p className="text-sm text-gray-700">
          {esAdopcion
            ? `Para enviar una solicitud de adopción de ${mascota.name} necesitas iniciar sesión.`
            : "Para enviarnos un mensaje desde aquí necesitas iniciar sesión."}{" "}
          Usaremos el nombre y el correo de tu cuenta.
        </p>
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={openLogin} className={BOTON_PRINCIPAL}>
            Inicia sesión para enviar
          </button>
          <button type="button" onClick={openRegister} className={BOTON_SECUNDARIO}>
            Crear cuenta
          </button>
          {onCerrar && (
            <button type="button" onClick={onCerrar} className={BOTON_SECUNDARIO}>
              Cerrar
            </button>
          )}
        </div>
      </div>
    );
  }

  // --- Enviada: solo llega aquí si la API respondió 201 ---
  if (estado === "enviada") {
    return (
      <div role="status" className="space-y-3 rounded-lg border border-green-300 bg-green-50 p-4 text-green-950">
        <h3 ref={enviadaRef} tabIndex={-1} className="flex items-center gap-2 font-semibold focus:outline-none">
          <CheckCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
          {esAdopcion ? "Solicitud enviada" : "Mensaje enviado"}
        </h3>
        <p className="text-sm">
          {esAdopcion ? "Tu solicitud quedó guardada" : "Tu mensaje quedó guardado"}
          {numero ? ` con el número ${numero}` : ""}. El equipo de PetConnect{" "}
          {esAdopcion ? "la" : "lo"} revisará y te escribirá al correo de tu cuenta (
          <span className="break-all">{user.email}</span>).
        </p>
        {onCerrar && (
          <button type="button" onClick={onCerrar} className={BOTON_SECUNDARIO}>
            Cerrar
          </button>
        )}
      </div>
    );
  }

  const enviando = estado === "enviando";
  const largo = mensaje.trim().length;

  return (
    <form onSubmit={enviar} noValidate className="space-y-4 rounded-lg border border-gray-200 p-4">
      <h3 className="font-semibold">
        {esAdopcion ? `Solicitud de adopción de ${mascota.name}` : "Escríbenos"}
      </h3>

      <p className="text-sm text-gray-700">
        Envías como <strong>{user.name}</strong> (<span className="break-all">{user.email}</span>).
      </p>

      {esAdopcion && (
        <div>
          <label htmlFor={id("telefono")} className="mb-1 block text-sm font-medium">
            Teléfono <span className="font-normal text-gray-600">(opcional)</span>
          </label>
          <input
            ref={telefonoRef}
            id={id("telefono")}
            name="telefono"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            maxLength={20}
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            aria-invalid={campoConError === "telefono" || undefined}
            aria-describedby={campoConError === "telefono" ? id("error") : undefined}
            className={CAMPO}
          />
        </div>
      )}

      <div>
        <label htmlFor={id("mensaje")} className="mb-1 block text-sm font-medium">
          {esAdopcion ? `¿Por qué quieres adoptar a ${mascota.name}?` : "Mensaje"}
        </label>
        <textarea
          ref={mensajeRef}
          id={id("mensaje")}
          name="mensaje"
          rows={5}
          required
          maxLength={MENSAJE_MAX}
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          aria-invalid={campoConError === "mensaje" || undefined}
          aria-describedby={`${id("ayuda")}${campoConError === "mensaje" ? ` ${id("error")}` : ""}`}
          className={`${CAMPO} resize-y`}
        />
        <p id={id("ayuda")} className="mt-1 flex justify-between gap-3 text-xs text-gray-600">
          <span>
            Entre {MENSAJE_MIN} y {MENSAJE_MAX} caracteres.
          </span>
          <span className="tabular-nums" aria-hidden="true">
            {largo}/{MENSAJE_MAX}
          </span>
        </p>
      </div>

      {/* Aviso B.5 del borrador de la política (versión 1.1): informa la finalidad (Ley 1581, art. 12) */}
      <p id={id("aviso")} className="text-xs leading-relaxed text-gray-600">
        Al enviar, usaremos tu nombre, tu correo
        {esAdopcion ? ", tu teléfono (si lo escribes)" : ""} y este mensaje para{" "}
        {esAdopcion ? `gestionar tu solicitud de adopción de ${mascota.name}` : "responder tu consulta"}, según la{" "}
        <Link
          to="/politica-de-datos"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-gray-900 underline underline-offset-2"
        >
          Política de tratamiento de datos personales
        </Link>
        . Solo el equipo de PetConnect lee tu mensaje. No escribas datos sensibles (salud, creencias…). Puedes
        pedir que lo borremos escribiendo a{" "}
        <a href={`mailto:${CORREO_ATENCION}`} className="break-all font-medium text-gray-900 underline underline-offset-2">
          {CORREO_ATENCION}
        </a>
        .
      </p>

      {error && (
        <div
          ref={errorRef}
          id={id("error")}
          role="alert"
          tabIndex={-1}
          className="space-y-2 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 focus:outline-2 focus:outline-offset-2 focus:outline-red-700"
        >
          <p>{error}</p>
          {volverAEntrar && (
            <button type="button" onClick={volverAIniciarSesion} className={BOTON_SECUNDARIO}>
              Volver a iniciar sesión
            </button>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={enviando} aria-describedby={id("aviso")} className={`${BOTON_PRINCIPAL} flex-1`}>
          <Send className="h-4 w-4" aria-hidden="true" />
          {enviando ? "Enviando…" : esAdopcion ? "Enviar solicitud" : "Enviar mensaje"}
        </button>
        {onCerrar && (
          <button type="button" onClick={onCerrar} disabled={enviando} className={BOTON_SECUNDARIO}>
            Cerrar
          </button>
        )}
      </div>
    </form>
  );
}
