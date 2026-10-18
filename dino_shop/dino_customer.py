import flet as ft
import requests
import ssl
import os

# این دو خط باعث می‌شوند پایتون تایید SSL را نادیده بگیرد
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''

# آدرس گوگل اسکریپت خود را اینجا جایگزین کنید
API_URL = "https://script.google.com/macros/s/AKfycbwVkcIn12GJ-8GQTVa-eOD8ijhU6zTbPi3qlCGCKj-Vxsu0Wksy7QUg3nzTFM442HQ52g/exec"

class DinoCustomerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Dino Shop - Customer App"
        self.page.rtl = True
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        self.cart = []
        self.products = []
        
        # ظرف اصلی برای نمایش صفحات مختلف (List یا Detail)
        self.main_container = ft.Container(expand=True)
        
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        self.page.appbar = ft.AppBar(
            title=ft.Text("Dino Shop "),
            center_title=True,
            bgcolor=ft.colors.AMBER_ACCENT_700,
            actions=[
                ft.IconButton(
                    icon=ft.icons.SHOPPING_CART,
                    on_click=self.show_cart_dialog
                )
            ]
        )
        
        self.page.add(self.main_container)

    def show_snack_bar_custom(self, message):
        """تابع کمکی برای نمایش پیام‌های پایین صفحه"""
        self.page.show_snack_bar(ft.SnackBar(ft.Text(message)))

    def load_products(self):
        self.main_container.content = ft.Column([ft.ProgressBar(), ft.Text("در حال بارگذاری...")], alignment="center")
        self.page.update()
        
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                self.products = response.json()
                self.show_product_grid()
            else:
                self.show_snack_bar_custom("خطا در اتصال به سرور")
        except Exception as e:
            self.show_snack_bar_custom(f"خطای شبکه: {e}")

    def show_product_grid(self):
        grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=0.7,
            spacing=10,
            run_spacing=10,
        )

        for prod in self.products:
            grid.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Image(src=prod['image_url'], height=120, fit=ft.ImageFit.COVER, border_radius=10),
                            ft.Text(prod['name'], weight="bold", size=14, max_lines=1),
                            ft.Text(f"{prod['price']:,} تومان", color=ft.colors.AMBER_700),
                            ft.ElevatedButton(
                                "جزئیات", 
                                icon=ft.icons.INFO_OUTLINE,
                                on_click=lambda e, p=prod: self.show_product_details(p),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )
            )
        
        self.main_container.content = ft.Column([grid], scroll=ft.ScrollMode.AUTO)
        self.page.update()

    def show_product_details(self, product):
        """نمایش صفحه جزئیات محصول"""
        detail_view = ft.Column([
            ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: self.show_product_grid()),
                ft.Text("جزئیات محصول", size=20, weight="bold")
            ]),
            ft.Image(src=product['image_url'], height=250, fit=ft.ImageFit.CONTAIN),
            ft.Text(product['name'], size=24, weight="bold"),
            ft.Text(f"{product['price']:,} تومان", size=20, color=ft.colors.AMBER_700),
            ft.Divider(),
            ft.Text(product['description'], size=16),
            ft.Text(f"ابعاد: {product.get('dimensions', 'نامشخص')}", italic=True, color=ft.colors.GREY_500),
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton(
                    "افزودن به سبد خرید",
                    icon=ft.icons.ADD_SHOPPING_CART,
                    on_click=lambda _: self.add_to_cart(product),
                    style=ft.ButtonStyle(bgcolor=ft.colors.AMBER_700, color=ft.colors.WHITE)
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], scroll=ft.ScrollMode.AUTO)

        self.main_container.content = detail_view
        self.page.update()

    def add_to_cart(self, product):
        self.cart.append(product)
        self.show_snack_bar_custom(f"{product['name']} به سبد اضافه شد")
        self.page.update()

    def show_cart_dialog(self, e):
        if not self.cart:
            self.show_snack_bar_custom("سبد خرید خالی است!")
            return

        total = sum(item['price'] for item in self.cart)
        cart_items_text = "\n".join([f"{item['name']} - {item['price']:,} تومان" for item in self.cart])

        def submit_order(e):
            # در اینجا فرم ثبت اطلاعات مشتری (نام و تلفن) را نمایش می‌دهیم
            self.show_order_form(total)

        dlg = ft.AlertDialog(
            title=ft.Text("سبد خرید شما"),
            content=ft.Column([
                ft.Text(cart_items_text),
                ft.Divider(),
                ft.Text(f"جمع کل: {total:,} تومان", weight="bold", size=18),
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("انصراف", on_click=lambda _: self.page.close(dlg)),
                ft.ElevatedButton("ادامه جهت ثبت سفارش", on_click=lambda _: self.submit_order_flow(dlg, total))
            ]
        )
        self.page.open(dlg)

    def submit_order_flow(self, dlg, total):
        self.page.close(dlg)
        self.show_order_form(total)

    def show_order_form(self, total):
        name_input = ft.TextField(label="نام و نام خانوادگی")
        phone_input = ft.TextField(label="شماره تماس", keyboard_type=ft.KeyboardType.PHONE)

        def on_submit(e):
            if not name_input.value or not phone_input.value:
                self.show_snack_bar_custom("لطفاً همه فیلدها را پر کنید")
                return
            
            # آماده‌سازی داده برای ارسال به گوگل اسکریپت
            order_data = {
                "customer_name": name_input.value,
                "phone": phone_input.value,
                "items": ", ".join([item['name'] for item in self.cart]),
                "total_price": total
            }

            try:
                response = requests.post(API_URL, json=order_data)
                if response.status_code == 200:
                    self.show_snack_bar_custom("🎉 سفارش با موفقیت ثبت شد!")
                    self.cart = [] # خالی کردن سبد
                    self.show_product_grid()
                else:
                    self.show_snack_bar_custom("خطا در ثبت سفارش")
            except Exception as ex:
                self.show_snack_bar_custom(f"خطای شبکه: {ex}")

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("ثبت نهایی سفارش"),
            content=ft.Column([
                name_input,
                phone_input,
            ], tight=True),
            actions=[
                ft.TextButton("بازگشت", on_click=lambda _: self.page.close(self.page.dialog)),
                ft.ElevatedButton("تایید و ارسال", on_click=on_submit)
            ]
        )
        self.page.open(self.page.dialog)

def main(page: ft.Page):
    DinoCustomerApp(page)

if __name__ == "__main__":
    ft.app(target=main)
