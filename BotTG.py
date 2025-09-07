#!/usr/bin/env python3
"""
PodarkaBotUz - Telegram Sovg'alar Xabardorisi
Gift Alerts kanalini kuzatib, yangi sovg'a bildirishnomalarini yuboradi
"""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
import time
import os
import sqlite3
from datetime import datetime
import json
import shutil

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sovga_xabardori.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def show_banner():
    """PodarkaBotUz banner ko'rsatadi"""
    print("\n" + "="*60)
    print("██████╗  ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗ █████╗ ")
    print("██╔══██╗██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗")
    print("██████╔╝██║   ██║██║  ██║███████║██████╔╝█████╔╝ ███████║")
    print("██╔═══╝ ██║   ██║██║  ██║██╔══██║██╔══██╗██╔═██╗ ██╔══██║")
    print("██║     ╚██████╔╝██████╔╝██║  ██║██║  ██║██║  ██╗██║  ██║")
    print("╚═╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝")
    print("                    BOT UZ - Gift Alert System")
    print("="*60)
    print("🇺🇿 O'zbek Telegram Sovg'alar Xabardorisi")
    print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
    print("="*60)

def show_mode_selection():
    """Mode tanlash menyusini ko'rsatadi"""
    print("\n🎛️  REJIM TANLANG")
    print("="*40)
    print("1️⃣  Real Mode - Haqiqiy sovg'a kuzatuvi")
    print("2️⃣  Test Mode - Sinov rejimi")
    print("3️⃣  Reset - Barcha ma'lumotlarni o'chirish")
    print("="*40)
    
    while True:
        try:
            choice = input("Rejimni tanlang (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("❌ Faqat 1, 2 yoki 3 ni tanlang!")
        except KeyboardInterrupt:
            print("\n👋 Bot to'xtatildi")
            exit(0)

def reset_all_data():
    """Barcha ma'lumotlar va fayllarni o'chiradi"""
    print("\n🗑️  BARCHA MA'LUMOTLARNI O'CHIRISH")
    print("="*50)
    print("⚠️  OGOHLANTIRISH: Bu operatsiya qaytarilmas!")
    print("📋 O'chiriladigan fayllar:")
    print("   - Litsenziya tasdig'i")
    print("   - Foydalanuvchi sozlamalari")
    print("   - Telegram sessiyalari")
    print("   - Log fayllari")
    
    confirm = input("\nRostdan ham o'chirmoqchimisiz? (ha/yo'q): ").strip().lower()
    if confirm not in ['ha', 'yes', 'y']:
        print("❌ Bekor qilindi.")
        return False
    
    # O'chiriladigan fayllar ro'yxati
    files_to_delete = [
        '.validated_key',
        'user_config.json',
        'sovga_session.session',
        'sovga_session.session-journal',
        'sovga_xabardori.log'
    ]
    
    deleted_count = 0
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ {file_path} o'chirildi")
                deleted_count += 1
            except Exception as e:
                print(f"❌ {file_path} ni o'chirib bo'lmadi: {e}")
        else:
            print(f"ℹ️  {file_path} topilmadi")
    
    print(f"\n🧹 Tozalash yakunlandi! {deleted_count} ta fayl o'chirildi")
    print("🔄 Botni qayta ishga tushiring...")
    return True

class SovgaXabardorisi:
    def __init__(self, mode='real'):
        # Kalit tizimi
        self.correct_key = "11111"
        self.key_file = ".validated_key"
        self.config_file = "user_config.json"
        
        # Bot rejimi
        self.mode = mode
        
        # Telegram API ma'lumotlari
        self.api_id = None
        self.api_hash = None
        self.phone = None
        
        # Kanal sozlamalari
        self.channel_name = "Gift_Alerts"  # Real mode uchun default
        self.test_channel_name = None      # Test mode uchun foydalanuvchi kiritadi
        self.target_username = None        # Foydalanuvchi kiritadi
        
        # Trigger matn - ikkala rejim uchun bir xil
        self.trigger_text = "A new gift has been added"
        
        # Mijoz sozlamalari
        self.client = None
        self.target_user = None
        
        # Spam nazorati
        self.is_spamming = False
        self.spam_task = None
        
    def check_key_validation(self):
        """Kalit tasdiqlangan yoki yo'qligini tekshiradi"""
        return os.path.exists(self.key_file)
    
    def save_key_validation(self):
        """Kalit tasdiqlangani haqida ma'lumot saqlaydi"""
        with open(self.key_file, 'w') as f:
            f.write(f"validated_at:{datetime.now().isoformat()}")
        logger.info("✅ Kalit tasdiqlandi va saqlandi")
    
    def load_user_config(self):
        """Foydalanuvchi konfiguratsiyasini yuklaydi"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_id = config.get('api_id')
                    self.api_hash = config.get('api_hash') 
                    self.phone = config.get('phone')
                    self.target_username = config.get('target_username')
                    self.test_channel_name = config.get('test_channel_name')
                    return True
            except Exception as e:
                logger.error(f"❌ Konfiguratsiya faylini yuklashda xatolik: {e}")
        return False
    
    def save_user_config(self):
        """Foydalanuvchi konfiguratsiyasini saqlaydi"""
        config = {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'phone': self.phone,
            'target_username': self.target_username,
            'test_channel_name': self.test_channel_name
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("✅ Foydalanuvchi sozlamalari saqlandi")
            return True
        except Exception as e:
            logger.error(f"❌ Sozlamalarni saqlashda xatolik: {e}")
            return False
    
    def validate_key(self):
        """Kalitni tasdiqlaydi"""
        print("\n🔐 LITSENZIYA TEKSHIRUVI")
        print("=" * 40)
        
        while True:
            entered_key = input("🔑 Litsenziya kalitini kiriting: ").strip()
            
            if entered_key == self.correct_key:
                print("✅ KALIT TO'G'RI! Litsenziya tasdiqlandi.")
                self.save_key_validation()
                return True
            else:
                print("❌ NOTO'G'RI KALIT! Qayta urinib ko'ring.")
                retry = input("Davom etishni xohlaysizmi? (ha/yo'q): ").strip().lower()
                if retry in ['yo\'q', 'yoq', 'n', 'no']:
                    return False
    
    def setup_user_api(self):
        """Foydalanuvchi API ma'lumotlarini sozlaydi"""
        print("\n🔧 TELEGRAM API SOZLAMALARI")
        print("=" * 50)
        print("1. https://my.telegram.org saytiga o'ting")
        print("2. Telefon raqamingiz bilan kiring")
        print("3. 'API Development Tools' → Yangi dastur yarating")
        print("4. API ID va API Hash ni oling")
        
        # API ID ni olish
        while True:
            try:
                api_id_input = input("\n🔢 API ID ni kiriting: ").strip()
                self.api_id = int(api_id_input)
                break
            except ValueError:
                print("❌ API ID raqam bo'lishi kerak.")
        
        # API Hash ni olish
        self.api_hash = input("🔐 API Hash ni kiriting: ").strip()
        
        # Telefon raqamini olish
        self.phone = input("📞 Telefon raqamini kiriting (+998901234567): ").strip()
        
        return True
    
    def get_target_user(self):
        """Kimga xabar yuborishni so'raydi"""
        print("\n👤 XABAR QABUL QILUVCHINI TANLANG")
        print("=" * 40)
        
        while True:
            username_input = input("👤 Kimga xabar yubormoqchisiz? (@username): ").strip()
            
            # @ belgisini tekshirish
            if not username_input.startswith('@'):
                print("❌ Username @ belgisi bilan boshlanishi kerak. Masalan: @username")
                continue
            
            # @ ni olib tashlash
            self.target_username = username_input[1:]  # @ ni olib tashlaydi
            
            print(f"✅ Tanlangan foydalanuvchi: @{self.target_username}")
            confirm = input("To'g'ri? (ha/yo'q): ").strip().lower()
            if confirm in ['ha', 'yes', 'y']:
                return True
    
    def get_test_channel(self):
        """Test rejimi uchun kanal linkini so'raydi"""
        print("\n📺 TEST KANALI TANLASH")
        print("=" * 40)
        print("📝 Test uchun kanal linkini kiriting")
        print("💡 Masalan: t.me/example yoki @example")
        
        while True:
            channel_input = input("📺 Kanal linkini kiriting: ").strip()
            
            # Link formatini tekshirish va tozalash
            if channel_input.startswith('t.me/'):
                # t.me/channel -> channel
                self.test_channel_name = channel_input.replace('t.me/', '')
            elif channel_input.startswith('@'):
                # @channel -> channel
                self.test_channel_name = channel_input[1:]
            elif channel_input.startswith('https://t.me/'):
                # https://t.me/channel -> channel
                self.test_channel_name = channel_input.replace('https://t.me/', '')
            else:
                # Faqat kanal nomi
                self.test_channel_name = channel_input
            
            print(f"✅ Test kanali: @{self.test_channel_name}")
            confirm = input("To'g'ri? (ha/yo'q): ").strip().lower()
            if confirm in ['ha', 'yes', 'y']:
                return True
    
    def cleanup_session(self):
        """Qulflangan sessiya fayllarini tozalaydi"""
        session_files = ['sovga_session.session', 'sovga_session.session-journal']
        for file in session_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    logger.info(f"🧹 {file} o'chirildi")
                except Exception as e:
                    logger.warning(f"⚠️ {file} ni o'chirib bo'lmadi: {e}")
    
    async def initialize_client(self):
        """Telegram mijozini ishga tushiradi"""
        try:
            session_name = 'sovga_session'
            
            try:
                self.client = TelegramClient(session_name, self.api_id, self.api_hash)
                await self.client.start(phone=self.phone)
            except Exception as session_error:
                if "database is locked" in str(session_error).lower():
                    logger.warning("🔒 Sessiya bazasi qulflangan, tozalanmoqda...")
                    await self.client.disconnect() if self.client else None
                    self.cleanup_session()
                    
                    logger.info("🔄 Yangi sessiya bilan qayta urinilmoqda...")
                    self.client = TelegramClient(session_name, self.api_id, self.api_hash)
                    await self.client.start(phone=self.phone)
                else:
                    raise session_error
            
            logger.info("✅ Telegram ga muvaffaqiyatli ulanildi")
            
            # Maqsadli foydalanuvchini topish
            try:
                self.target_user = await self.client.get_entity(self.target_username)
                logger.info(f"✅ Foydalanuvchi topildi: @{self.target_username}")
            except Exception as e:
                logger.error(f"❌ @{self.target_username} foydalanuvchisi topilmadi: {e}")
                print(f"❌ @{self.target_username} foydalanuvchisi topilmadi!")
                print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
                return False
                
            return True
            
        except SessionPasswordNeededError:
            password = input("🔐 Ikki bosqichli parolni kiriting: ")
            await self.client.sign_in(password=password)
            return True
            
        except Exception as e:
            logger.error(f"❌ Ulanishda xatolik: {e}")
            print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
            return False
    
    async def start_spam(self, original_message_text):
        """Spam xabarlarini yuboradi"""
        self.is_spamming = True
        spam_count = 0
        max_spam = 50 if self.mode == 'real' else 5  # Test rejimida kam spam
        
        logger.info(f"🚨 SPAM BOSHLANDI ({self.mode.upper()} MODE) - Maksimal {max_spam} ta xabar")
        
        while self.is_spamming and spam_count < max_spam:
            spam_count += 1
            
            if self.mode == 'test':
                spam_text = f"🧪 TEST SPAM #{spam_count}/{max_spam} 🧪\n\n" \
                           f"Test kanali: @{self.test_channel_name}\n" \
                           f"Topilgan xabar: {original_message_text[:100]}...\n\n" \
                           f"⚠️ To'xtatish uchun 'To'xta' yozing!\n" \
                           f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            else:
                spam_text = f"🚨 SOVG'A OGOHLANTIRUVI #{spam_count}/{max_spam} 🚨\n\n" \
                           f"Asl xabar: {original_message_text[:100]}...\n\n" \
                           f"⚠️ To'xtatish uchun 'To'xta' yozing!\n" \
                           f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            try:
                await self.client.send_message(self.target_user, spam_text)
                logger.info(f"📢 Spam #{spam_count} yuborildi")
            except Exception as e:
                logger.error(f"❌ Spam #{spam_count} yuborishda xatolik: {e}")
            
            await asyncio.sleep(2)
        
        if spam_count >= max_spam and self.is_spamming:
            self.is_spamming = False
            if self.mode == 'test':
                await self.client.send_message(
                    self.target_user,
                    f"🧪 TEST YAKUNLANDI - {max_spam} ta xabar yuborildi!"
                )
            else:
                await self.client.send_message(
                    self.target_user,
                    f"⚠️ {max_spam} TA XABAR YUBORILDI!\n🎁 Umid qilamanki sovg'ani ko'rdingiz!"
                )
    
    async def stop_spam(self):
        """Spamni to'xtatadi"""
        if self.is_spamming:
            self.is_spamming = False
            if self.spam_task:
                self.spam_task.cancel()
            
            if self.mode == 'test':
                await self.client.send_message(
                    self.target_user,
                    "✅ TEST SPAM TO'XTATILDI! 🧪"
                )
            else:
                await self.client.send_message(
                    self.target_user,
                    "✅ SPAM TO'XTATILDI! Sovg'ani olishda omad! 🎁"
                )
            logger.info("✅ Spam to'xtatildi")
    
    async def setup_stop_listener(self):
        """'To'xta' xabarini tinglovchi"""
        @self.client.on(events.NewMessage(from_users=self.target_user))
        async def stop_handler(event):
            message_text = event.message.text or ""
            
            if message_text.lower().strip() in ['to\'xta', 'toxta', 'stop']:
                logger.info("🛑 TO'XTA buyrug'i qabul qilindi")
                await self.stop_spam()

    async def forward_message_and_alert(self, message):
        """Sovg'a xabarini yuboradi va spam boshlaydi"""
        try:
            # Xabarni jo'natish
            await self.client.forward_messages(
                entity=self.target_user,
                messages=message,
                from_peer=message.peer_id
            )
            
            logger.info(f"✅ Xabar @{self.target_username} ga jo'natildi")
            
            # Ogohlantirish
            if self.mode == 'test':
                alert_text = f"🧪 TEST XABARI TOPILDI! 🧪\n\nKanal: @{self.test_channel_name}\nXabar: {message.text}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n⚠️ To'xtatish uchun 'To'xta' javob bering!"
            else:
                alert_text = f"🎁 SOVG'A OGOHLANTIRUVI! 🎁\n\n{message.text}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n⚠️ To'xtatish uchun 'To'xta' javob bering!"
            
            await self.client.send_message(self.target_user, alert_text)
            
            # Spam boshlash
            self.spam_task = asyncio.create_task(self.start_spam(message.text))
                
        except Exception as e:
            logger.error(f"❌ Xabar yuborishda xatolik: {e}")
    
    async def start_monitoring(self):
        """Kanallarni kuzatadi"""
        try:
            # Kanal nomini aniqlash
            channel_to_monitor = self.test_channel_name if self.mode == 'test' else self.channel_name
            
            # Kanalni topish
            channel = None
            try:
                channel = await self.client.get_entity(channel_to_monitor)
                logger.info(f"✅ Kanal topildi: @{channel_to_monitor}")
            except Exception:
                try:
                    channel = await self.client.get_entity(f"@{channel_to_monitor}")
                    logger.info(f"✅ Kanal topildi: @{channel_to_monitor}")
                except Exception as e:
                    logger.error(f"❌ @{channel_to_monitor} kanali topilmadi: {e}")
                    print(f"❌ @{channel_to_monitor} kanali topilmadi!")
                    print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
                    return
            
            # To'xta tinglovchisini sozlash
            await self.setup_stop_listener()
            
            # Yangi xabarlar handler
            @self.client.on(events.NewMessage(chats=channel))
            async def gift_handler(event):
                message_text = event.message.text or ""
                
                if self.trigger_text.lower() in message_text.lower():
                    if self.mode == 'test':
                        logger.info(f"🧪 TEST: '@{self.test_channel_name}' kanalida trigger topildi!")
                    else:
                        logger.info("🎁 SOVG'A ANIQLANDI!")
                    await self.forward_message_and_alert(event.message)
            
            # Rejim ma'lumotlarini ko'rsatish
            if self.mode == 'test':
                logger.info(f"🧪 TEST REJIMI: @{self.test_channel_name} kanali kuzatilmoqda")
                logger.info(f"📬 Trigger: '{self.trigger_text}'")
                logger.info(f"💡 Test uchun @{self.test_channel_name} kanalida '{self.trigger_text}' matnini yozing")
            else:
                logger.info(f"🔍 REAL REJIMI: @{self.channel_name} kanali kuzatilmoqda")
                logger.info(f"📬 Trigger: '{self.trigger_text}'")
            
            logger.info(f"📬 Xabar qabul qiluvchi: @{self.target_username}")
            logger.info("💡 Spam to'xtatish uchun foydalanuvchi 'To'xta' yozishi kerak")
            logger.info("✨ Bot ishlayapti! To'xtatish uchun Ctrl+C bosing.\n")
            
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Bot to'xtatildi")
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
    
    async def test_connection(self):
        """Ulanishni sinaydi"""
        try:
            me = await self.client.get_me()
            logger.info(f"✅ Ulanildi: {me.first_name}")
            
            # Test xabari
            if self.mode == 'test':
                await self.client.send_message(
                    self.target_user,
                    f"🧪 PodarkaBotUz - TEST REJIMI ulanish muvaffaqiyatli!\n\nTest kanali: @{self.test_channel_name}\nTrigger: '{self.trigger_text}'\n\nTest uchun @{self.test_channel_name} kanalida '{self.trigger_text}' matnini yozing."
                )
            else:
                await self.client.send_message(
                    self.target_user,
                    "✅ PodarkaBotUz - REAL REJIMI ulanish muvaffaqiyatli!"
                )
            logger.info("✅ Test xabari yuborildi")
            
            return True
        except Exception as e:
            logger.error(f"❌ Test muvaffaqiyatsiz: {e}")
            return False

async def main():
    """Asosiy funksiya"""
    show_banner()
    
    # Mode tanlash
    selected_mode = show_mode_selection()
    
    # Reset rejimi
    if selected_mode == 3:
        if reset_all_data():
            return
        else:
            return
    
    # Rejimni aniqlash
    mode = 'real' if selected_mode == 1 else 'test'
    
    print(f"\n🎯 Tanlangan rejim: {'REAL MODE' if mode == 'real' else 'TEST MODE'}")
    
    notifier = SovgaXabardorisi(mode=mode)
    
    try:
        # Kalit tekshirish
        if not notifier.check_key_validation():
            if not notifier.validate_key():
                print("❌ Litsenziya tasdiqlanmadi.")
                return
        else:
            print("✅ Litsenziya tasdiqlangan.")
        
        # Konfiguratsiya yuklash yoki sozlash
        config_exists = notifier.load_user_config()
        
        if not config_exists or (mode == 'test' and not notifier.test_channel_name):
            print("\n🔧 Sozlamalar:")
            
            if not config_exists:
                if not notifier.setup_user_api():
                    print("❌ API sozlamalari xato.")
                    return
                
                if not notifier.get_target_user():
                    print("❌ Foydalanuvchi tanlanmadi.")
                    return
            
            # Test rejimi uchun kanal so'rash
            if mode == 'test':
                if not notifier.get_test_channel():
                    print("❌ Test kanali tanlanmadi.")
                    return
                
            if not notifier.save_user_config():
                print("❌ Sozlamalar saqlanmadi.")
                return
                
        else:
            print("✅ Sozlamalar yuklandi.")
        
        # Ulanish
        print("\n🔌 Ulanilmoqda...")
        if not await notifier.initialize_client():
            return
        
        # Test
        print("\n🧪 Test...")
        if not await notifier.test_connection():
            return
        
        # Kuzatuvni boshlash
        mode_name = "REAL REJIMI" if mode == 'real' else "TEST REJIMI"
        print(f"\n🚀 {mode_name} boshlandi...")
        await notifier.start_monitoring()
        
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
    finally:
        if notifier.client:
            try:
                await notifier.client.disconnect()
            except:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 PodarkaBotUz to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
