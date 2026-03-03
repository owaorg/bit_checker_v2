from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, RichLog
from textual.containers import Container, Vertical, Center
from textual.screen import Screen
from textual import on 
import aiohttp, asyncio
import json
import os

work_proxy = []
path = os.path.join(os.path.dirname(__file__), "settings", "settings.json")

class SettingsScrean(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Назад", id="Back")
        yield Input("Введите задержку", id="NewTimeOut")
        yield Input("Введите сайт для проверки прокси", id='NewSite')
        yield Input("Введите потоки", id='Potok')
        with Center():
            yield Button("Применить настройки", id="CompliteButton")

    @on(Button.Pressed, "#CompliteButton")
    def save_settings(self):
        with open(path, "w", encoding="utf-8") as file:
            new_site = self.query_one("#NewSite", Input).value
            new_timeout = self.query_one("#NewTimeOut").value
            potok = self.query_one("#Potok").value

            if not new_site:
                new_site = "https://www.google.com/"
            if not new_timeout:
                new_timeout = "2"
            if not potok:
                potok = 60

            zagotovok_json = f"""
{{
    "site": "{new_site}",
    "timeout": "{new_timeout}",
    "potok": "{potok}"
}}
            """
            file.write(zagotovok_json)
            self.notify("💪🏻 Настройки сохранены!")

    @on(Button.Pressed, "#Back")
    def back(self):
        self.app.pop_screen()

class bit_checker_v2(App):

    CSS_PATH = "css/style.tcss"
    SCREENS = {"settings": SettingsScrean}


    def inject_config(self):
        try:
            with open(path, 'r', encoding='utf-8') as file:
                file = json.load(file)

                site = file["site"]
                out = float(file["timeout"])
                potok = int(file["potok"])

                return site,out,potok
        except Exception as e:
            self.notify(f"[bold red] ❌ Ошибка! {e}")
            return "https://www.google.com/", 2, 60

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            with Vertical(id="input-area"):
                yield Input(placeholder="Путь к прокси...", id="Input")
                yield Button("Начать Проверку", id="Button", variant="primary")
            yield RichLog(id="output-window", highlight=True, markup=True)
            with Center():
                yield Button("Настройки", id="settings", variant="primary")
        yield Footer()

    async def checker_proxy(self,sem,session,current_proxy,site,out):
        log = self.query_one("#output-window", RichLog)

        async with sem:
            try:
                async with session.get(site, proxy=current_proxy, timeout=float(out)) as response:

                    log.write(f"[bold yellow]💪🏻 Проверяю прокси > {current_proxy}")
                    if response.status in [200, 201, 202, 204]:
                        log.write(f"[bold yellow]✨ Прокси работает! | {current_proxy}")
                        work_proxy.append(current_proxy)
                    else:
                        log.write(f"[bold red]🤷🏻 Прокси не работает! | {current_proxy}")
            except Exception as e:
                log.write(f"[bold red]❌ Фатальная ошибка прокси | {current_proxy} (Err: {type(e).__name__})[/]")

    @on(Button.Pressed, "#settings")
    def button_settings_click(self):
        self.push_screen("settings")
    
    @on(Button.Pressed, "#Button")
    async def click_button(self):

        log = self.query_one("#output-window", RichLog)

        site,out,semo = self.inject_config()

        sem = asyncio.Semaphore(semo)
        tasks = []

        path = self.query_one("#Input", Input).value

        if not path:
            log.write("f[bold yellow]✨ Пожалуйста, введите файл с прокси!")

        with open(path, 'r', encoding='utf-8') as file:
            file = file.read().splitlines()
            async with aiohttp.ClientSession() as session:
                for i in file:
                    current_proxy = f"http://{i}"
                                        
                    task = asyncio.create_task(self.checker_proxy(sem,session,current_proxy,site,out))
                    tasks.append(task)

            await asyncio.gather(*tasks)
                

        save_path = os.path.join(os.path.dirname(__file__), "work.txt")
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(work_proxy)) 
        
        log.write(f"[bold green]🏁 Готово! Результаты в work.txt")

        if not work_proxy:
            log.write(f"[bold yellow]🤷🏻 Упс, рабочих прокси нету...")

if __name__ == "__main__":
    bit_checker_v2().run()




        