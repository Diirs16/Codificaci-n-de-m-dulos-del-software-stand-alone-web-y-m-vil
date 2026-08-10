"""
Plantillas HTML de correo de PetConnect.

Basadas en tablas (compatibilidad con Outlook/Gmail) con la identidad real
de la aplicacion web: logo de 4 colores + tipografia negra/blanca.
"""

HTML_CODE = """
<div style="background:#f5f5f5;padding:32px 16px;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:480px;margin:0 auto;">
    <tr>
      <td style="height:6px;line-height:6px;font-size:0;border-radius:14px 14px 0 0;
                 background:linear-gradient(90deg,#4cc9d0,#7bc67e,#f5c242,#e8833a);">&nbsp;</td>
    </tr>
    <tr>
      <td style="background:#ffffff;border:1px solid #e8e8e8;border-top:none;
                 border-radius:0 0 14px 14px;padding:40px 36px;">

        <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" width="26">
                <tr>
                  <td width="12" height="12" style="background:#4cc9d0;border-radius:4px;font-size:0;">&nbsp;</td>
                  <td width="2"></td>
                  <td width="12" height="12" style="background:#e8833a;border-radius:4px;font-size:0;">&nbsp;</td>
                </tr>
                <tr><td colspan="3" height="2"></td></tr>
                <tr>
                  <td width="12" height="12" style="background:#8cc63f;border-radius:4px;font-size:0;">&nbsp;</td>
                  <td width="2"></td>
                  <td width="12" height="12" style="background:#f5c242;border-radius:4px;font-size:0;">&nbsp;</td>
                </tr>
              </table>
            </td>
            <td style="padding-left:10px;font-size:19px;font-weight:800;color:#111111;letter-spacing:-0.02em;">
              PetConnect
            </td>
          </tr>
        </table>

        <p style="color:#111111;font-size:16px;margin:0 0 6px;">Hola <strong>{name}</strong>,</p>
        <p style="color:#666666;font-size:14px;line-height:1.5;margin:0 0 24px;">{proposito}</p>

        <div style="background:#111111;border-radius:12px;padding:22px 12px;text-align:center;margin-bottom:22px;">
          <span style="font-size:34px;font-weight:800;letter-spacing:9px;color:#ffffff;
                       font-family:'SF Mono',Consolas,monospace;">{code}</span>
        </div>

        <p style="color:#999999;font-size:12px;line-height:1.6;text-align:center;margin:0;">
          Expira en <strong style="color:#666666;">10 minutos</strong>.<br>
          Si no solicitaste esto, ignora este mensaje.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding-top:20px;text-align:center;color:#bbbbbb;font-size:11px;">
        Pet Connect &middot; Tu tienda de confianza para productos de mascotas y adopcion responsable
      </td>
    </tr>
  </table>
</div>"""

HTML_WELCOME = """
<div style="background:#f5f5f5;padding:32px 16px;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:480px;margin:0 auto;">
    <tr>
      <td style="height:6px;line-height:6px;font-size:0;border-radius:14px 14px 0 0;
                 background:linear-gradient(90deg,#4cc9d0,#7bc67e,#f5c242,#e8833a);">&nbsp;</td>
    </tr>
    <tr>
      <td style="background:#ffffff;border:1px solid #e8e8e8;border-top:none;
                 border-radius:0 0 14px 14px;padding:40px 36px;text-align:center;">

        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" width="26">
                <tr>
                  <td width="12" height="12" style="background:#4cc9d0;border-radius:4px;font-size:0;">&nbsp;</td>
                  <td width="2"></td>
                  <td width="12" height="12" style="background:#e8833a;border-radius:4px;font-size:0;">&nbsp;</td>
                </tr>
                <tr><td colspan="3" height="2"></td></tr>
                <tr>
                  <td width="12" height="12" style="background:#8cc63f;border-radius:4px;font-size:0;">&nbsp;</td>
                  <td width="2"></td>
                  <td width="12" height="12" style="background:#f5c242;border-radius:4px;font-size:0;">&nbsp;</td>
                </tr>
              </table>
            </td>
            <td style="padding-left:10px;font-size:19px;font-weight:800;color:#111111;letter-spacing:-0.02em;">
              PetConnect
            </td>
          </tr>
        </table>

        <p style="font-size:22px;font-weight:800;color:#111111;margin:0 0 10px;line-height:1.3;">
          &iexcl;Bienvenido a la familia PetConnect, {name}!
        </p>
        <p style="font-size:15px;color:#666666;margin:0 0 28px;line-height:1.5;">
          Todo para tu mascota en un solo lugar &mdash; productos de calidad<br>
          y un programa de adopci&oacute;n responsable.
        </p>

        <a href="http://localhost:5173" style="display:inline-block;background:#111111;color:#ffffff;
           text-decoration:none;font-weight:700;font-size:14px;padding:14px 32px;border-radius:10px;">
          Explorar PetConnect
        </a>

        <p style="color:#bbbbbb;font-size:12px;margin:28px 0 0;">
          Gracias por unirte. Estamos felices de tenerte aqu&iacute; 🐾
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding-top:20px;text-align:center;color:#bbbbbb;font-size:11px;">
        Pet Connect &middot; Tu tienda de confianza para productos de mascotas y adopcion responsable
      </td>
    </tr>
  </table>
</div>"""
