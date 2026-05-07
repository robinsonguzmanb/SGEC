import ollama
def get_master_prompt(reglas_grado, saldo_disponible, logica_renta=""):
    return f"""Eres un Auditor Experto en Compensaciones con un tono profesional, analítico y preventivo. 
Tu trabajo es simular escenarios de cambios organizacionales y validar la coherencia de la clasificación de grados salariales y velar por los recursos financieros de la empresa.
A continuación, las reglas de grado actuales extraídas de nuestra base de datos:
{reglas_grado}

REGLAS DE CÁLCULO DE RENTAS:
{logica_renta}

EL SALDO DISPONIBLE EN EL CECO DEL COLABORADOR ES: ${saldo_disponible:,.2f}
INSTRUCCIONES CRÍTICAS Y REGLAS DE BLOQUEO:
1. "The Budget Lock" (Falta de Presupuesto):
Si la propuesta salarial que sugiere o infiere el usuario para el colaborador requiere un aumento, y ese incremento supera el saldo disponible en el CECO, DEBES interrumpir la simulación.
Comienza tu respuesta EXACTAMENTE con la palabra "[PRESUPUESTO_EXCEDIDO]" seguido de "Operación bloqueada por falta de presupuesto en el CECO. Fondos faltantes: $[diferencia]". Y pregúntale al usuario si desea proceder con una reserva parcial.
2. Discrepancia de Grado:
Analiza la descripción de tareas ingresada y compárala con el "Grado Actual".
Si las tareas exceden el nivel de grado, DEBES interrumpir la simulación. Comienza tu respuesta EXACTAMENTE con la palabra "[DISCREPANCIA_DETECTADA]", seguido de la explicación técnica y sugerencia de un grado adecuado.
Si ni el presupuesto ni el grado presentan problemas, asiste amablemente en la simulación al usuario.
"""
def simular_chat(contexto_empleado, reglas_grado, mensajes_historial, ceco_info, temperature=0.0):
    """
    Envía la conversación a Ollama y retorna la respuesta.
    ceco_info contiene los datos financieros para calcular el saldo.
    temperature ajusta la creatividad de la IA.
    """
    
    saldo_disponible = ceco_info['presupuesto_anual'] - ceco_info['presupuesto_consumido'] - ceco_info['presupuesto_reservado']
    
    system_prompt = get_master_prompt(reglas_grado, saldo_disponible)
    
    contexto_iniciado = f"""Contexto del Colaborador (Desidentificado):
- ID: {contexto_empleado['id_empleado']}
- Grado Actual: {contexto_empleado['grado_actual']}
- Sueldo Base actual: ${contexto_empleado['sueldo_base']}
- ID CECO: {contexto_empleado['id_ceco']}
Por favor evalúa la siguiente interacción teniendo en cuenta esta información y The Budget Lock."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": contexto_iniciado}
    ]
    
    messages.extend(mensajes_historial)
    
    try:
        response = ollama.chat(model='llama3', messages=messages, options={'temperature': temperature})
        return response['message']['content']
    except Exception as e:
        return f"[DISCREPANCIA_DETECTADA] Error interno de comunicación con motor local IA. Asegúrate que Ollama esté en ejecución. Detalle: {str(e)}"
def generar_borrador_correo(contexto_empleado, texto_explicacion, grado_sugerido):
    return f"""Asunto: Revisión de Grado Requerida - Caso {contexto_empleado['id_empleado']}
Estimado Analista de Compensaciones,
Por medio de la presente solicito la revisión formal de la clasificación de grado para el colaborador con ID {contexto_empleado['id_empleado']}.
Datos de contexto actuales:
- Grado Actual: {contexto_empleado['grado_actual']}
- Sueldo Base: {contexto_empleado['sueldo_base']}
- Centro de Costos: {contexto_empleado['id_ceco']}
El motor de inteligencia local ha detectado una inconsistencia entre la descripción de tareas propuesta y el grado actual.
Grado Sugerido por IA: {grado_sugerido}
Justificación Técnica:
{texto_explicacion}
Quedo a la espera de sus comentarios para proceder con la simulación en el SGEC.
Saludos Cordiales,
[Usuario Admin]"""
