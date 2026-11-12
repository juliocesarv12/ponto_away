import logging
import re

from dataclasses import dataclass

from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from src.config import Settings, only_digits, redact
from src.texto import opcoes_de_matricula, resumo_consulta, resumo_registro

log = logging.getLogger("ponto")


@dataclass
class PontoResult:
    ok: bool
    message: str
    screenshot: bytes | None = None


async def registrar_ponto(settings: Settings, matricula: str | None, *, apenas_consulta: bool) -> PontoResult:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        page: Page | None = None
        try:
            context = await browser.new_context(
                locale="pt-BR",
                timezone_id=settings.timezone,
                viewport={"width": 1440, "height": 900},
            )
            page = await context.new_page()
            page.set_default_timeout(25_000)
            page.set_default_navigation_timeout(50_000)

            log.info("abrindo %s", settings.portal_url)
            await page.goto(settings.portal_url, wait_until="domcontentloaded")
            await _aceitar_cookies(page)
            await _login(page, settings)
            await _abrir_registrar_ponto(page)

            aviso = await _escolher_matricula(page, matricula or settings.matricula)
            if aviso:
                return PontoResult(False, aviso, await _shot(page))

            if apenas_consulta:
                texto = await _texto_util(page)
                return PontoResult(True, resumo_consulta(texto), await _shot(page))

            await _clicar_registrar(page)
            await _confirmar(page)
            texto = await _texto_util(page)
            return PontoResult(True, resumo_registro(texto), await _shot(page))
        except Exception as exc:
            log.exception("falha no fluxo do ponto")
            shot = await _shot(page) if page else None
            mensagem = redact(str(exc), settings.senha).split("\n", 1)[0]
            return PontoResult(
                False,
                f"Não consegui concluir: {mensagem[:400]}",
                shot,
            )
        finally:
            await browser.close()


async def _aceitar_cookies(page: Page) -> None:
    botao = page.get_by_role("button", name=re.compile(r"^aceito$", re.I))
    try:
        if await botao.count():
            await botao.first.click(timeout=3_000)
    except PlaywrightTimeout:
        return


async def _login(page: Page, settings: Settings) -> None:
    if "sauron" not in page.url:
        link = page.get_by_role("link", name=re.compile(r"login com o sauron", re.I))
        await link.first.click()
        await page.wait_for_url(re.compile(r"sauron"), timeout=30_000)

    usuario = page.locator("#validation-login #Username")
    await usuario.click()
    await usuario.fill("")
    await usuario.press_sequentially(settings.cpf, delay=30)
    valor = await usuario.input_value()
    if only_digits(valor) != settings.cpf:
        await usuario.fill(settings.cpf)

    await page.locator("#validation-login #Password").fill(settings.senha)
    await page.locator("#validation-login").get_by_role("button", name=re.compile(r"^entrar$", re.I)).click()

    try:
        await page.wait_for_url(
            re.compile(r"https://portaldoservidor\.sistemas\.ro\.gov\.br(?!.*[Aa]utenticacao)"),
            timeout=50_000,
        )
    except PlaywrightTimeout:
        erro = await _erros_visiveis(page)
        raise RuntimeError(erro or "O login não saiu da tela do SAURON. Confere CPF e senha.") from None

    await _aceitar_cookies(page)
    log.info("login ok, url=%s", page.url)


async def _abrir_registrar_ponto(page: Page) -> None:
    botao = _botao_registrar(page)
    if not await botao.count() or not await botao.first.is_visible():
        menu = page.get_by_role("link", name=re.compile(r"registrar\s+ponto", re.I))
        if not await menu.count():
            menu = page.get_by_text(re.compile(r"registrar\s+ponto", re.I))
        try:
            await menu.first.wait_for(timeout=30_000)
        except PlaywrightTimeout:
            raise RuntimeError(
                "Não achei o menu Registrar ponto. Se ele não aparece no portal, o RH precisa liberar essa opção."
            ) from None
        await menu.first.click()
    try:
        await botao.first.wait_for(timeout=20_000)
    except PlaywrightTimeout:
        raise RuntimeError("O botão Registrar não apareceu na tela de ponto.") from None
    log.info("tela de registro aberta, url=%s", page.url)


async def _escolher_matricula(page: Page, matricula: str | None) -> str | None:
    selects = page.locator("select")
    total_selects = await selects.count()
    for i in range(total_selects):
        select = selects.nth(i)
        textos = await select.locator("option").all_inner_texts()
        reais = opcoes_de_matricula(textos)
        if not reais:
            continue
        return await _aplicar_escolha(reais, matricula, lambda texto, select=select: select.select_option(label=texto))

    radios = page.locator("input[type=radio]")
    total = await radios.count()
    pares: list[tuple[Locator, str]] = []
    for i in range(total):
        radio = radios.nth(i)
        texto = " ".join((await _rotulo_do_radio(radio)).split())
        if texto:
            pares.append((radio, texto))
    reais_radio = opcoes_de_matricula([texto for _, texto in pares])
    if not reais_radio:
        return None
    por_texto = {texto: radio for radio, texto in pares}

    async def marcar(texto: str) -> None:
        await por_texto[texto].check()

    return await _aplicar_escolha(reais_radio, matricula, marcar)


async def _aplicar_escolha(opcoes: list[str], matricula: str | None, aplicar) -> str | None:
    if matricula:
        alvo = matricula.strip().lower()
        for texto in opcoes:
            if alvo in texto.lower():
                await aplicar(texto)
                return None
        return "Não achei essa matrícula. Opções:\n" + "\n".join(f"- {texto}" for texto in opcoes)
    if len(opcoes) == 1:
        await aplicar(opcoes[0])
        return None
    return (
        "Tem mais de uma matrícula. Manda /bater e o número, por exemplo /bater 12345.\n"
        + "\n".join(f"- {texto}" for texto in opcoes)
    )


async def _rotulo_do_radio(radio: Locator) -> str:
    radio_id = await radio.get_attribute("id")
    if radio_id:
        label = radio.page.locator(f"label[for='{radio_id}']")
        if await label.count():
            return await label.first.inner_text()
    pai = radio.locator("xpath=ancestor::label[1]")
    if await pai.count():
        return await pai.first.inner_text()
    return (await radio.get_attribute("value")) or ""


def _botao_registrar(page: Page) -> Locator:
    por_texto = page.locator("button, a").filter(has_text=re.compile(r"^\s*registrar\s*$", re.I))
    por_valor = page.locator(
        "input[type=submit][value=registrar i], input[type=button][value=registrar i]"
    )
    return por_texto.or_(por_valor)


async def _clicar_registrar(page: Page) -> None:
    botao = _botao_registrar(page)
    await botao.first.click()
    log.info("clique em registrar")


async def _confirmar(page: Page) -> None:
    certeza = page.get_by_role("button", name=re.compile(r"tenho certeza", re.I))
    try:
        await certeza.first.wait_for(state="visible", timeout=12_000)
        await certeza.first.click()
        log.info("confirmação enviada")
    except PlaywrightTimeout:
        swal = page.locator(".swal2-confirm")
        if await swal.count():
            await swal.first.click()
            return
        raise RuntimeError("O botão de confirmar (Sim, Tenho Certeza) não apareceu.") from None

    try:
        await page.get_by_text(re.compile(r"sucesso|registrad|erro|não foi|nao foi|atenção|atencao", re.I)).first.wait_for(
            timeout=15_000
        )
    except PlaywrightTimeout:
        log.info("sem mensagem explícita de sucesso; seguindo com o que estiver na tela")


async def _erros_visiveis(page: Page) -> str:
    partes: list[str] = []
    for seletor in (".text-danger", ".validation-summary-errors", ".toast-message", ".alert"):
        loc = page.locator(seletor)
        total = await loc.count()
        for i in range(min(total, 4)):
            texto = (await loc.nth(i).inner_text()).strip()
            if texto and texto not in partes:
                partes.append(texto)
    return " | ".join(partes)


async def _texto_util(page: Page) -> str:
    for seletor in ("main", ".content", "#content", "body"):
        loc = page.locator(seletor)
        if await loc.count():
            texto = await loc.first.inner_text()
            if texto.strip():
                return texto
    return ""


async def _shot(page: Page | None) -> bytes | None:
    if page is None:
        return None
    try:
        return await page.screenshot(full_page=True)
    except Exception:
        log.warning("não foi possível tirar screenshot", exc_info=True)
        return None
