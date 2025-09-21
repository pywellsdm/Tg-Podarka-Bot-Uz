#!/usr/bin/env python3
"""
PodarkaBotUz - Telegram Sovg'alar Xabardorisi
Gift Alerts kanalini kuzatib, yangi sovg'a bildirishnomalarini yuboradi
"""

import asyncio
import logging
from telethon import TelegramClient, events, functions
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
    print("4️⃣  Settings - Sozlamalar")
    print("="*40)
    
    while True:
        try:
            choice = input("Rejimni tanlang (1/2/3/4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Faqat 1, 2, 3 yoki 4 ni tanlang!")
        except KeyboardInterrupt:
            print("\n👋 Bot to'xtatildi")
            exit(0)

def show_settings_menu():
    """Sozlamalar menyusini ko'rsatadi"""
    print("\n⚙️  SOZLAMALAR")
    print("="*40)
    print("1️⃣  Verification - Telegram hisobni tasdiqlash")
    print("2️⃣  Target Username - Kimga xabar yuborish")
    print("3️⃣  Test Channel - Test kanali o'zgartirish")
    print("4️⃣  Back - Asosiy menyuga qaytish")
    print("="*40)
    
    while True:
        try:
            choice = input("Sozlamani tanlang (1/2/3/4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Faqat 1, 2, 3 yoki 4 ni tanlang!")
        except KeyboardInterrupt:
            print("\n👋 Bot to'xtatildi")
            exit(0)

def reset_all_data():
    """Barcha ma'lumotlar va fayllarni o'chiradi"""
    print("\n🗑️  BARCHA MA'LUMOTLARNI O'CHIRISH")
    print("="*50)
    print("⚠️  OGOHLANTIRISH: Bu operatsiya qaytarilmas!")
    print("📋 O'chiriladigan fayllar:")
    print("   - Foydalanuvchi sozlamalari")
    print("   - Telegram sessiyalari")
    print("   - Log fayllari")
    
    confirm = input("\nRostdan ham o'chirmoqchimisiz? (ha/yo'q): ").strip().lower()
    if confirm not in ['ha', 'yes', 'y']:
        print("❌ Bekor qilindi.")
        return False
    
    # O'chiriladigan fayllar ro'yxati
    files_to_delete = [
        'user_config.json',
        'sovga_session.session',
        'sovga_session.session-journal',
        'sovga_xabardori.log',
        'temp_join_session.session',
        'temp_join_session.session-journal'
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
        # Configuration file
        self.config_file = "user_config.json"
        
        # Bot rejimi
        self.mode = mode
        
        # HARDCODED Telegram API ma'lumotlari - Client's credentials
        self.api_id = 17134298
        self.api_hash = "4234aba41616e8de069a72f6d5940dec"
        self.phone = "+254728981704"
        
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
        """Always return True since no key validation needed"""
        return True
    
    def save_key_validation(self):
        """No key validation needed"""
        pass
    
    def load_user_config(self):
        """Foydalanuvchi konfiguratsiyasini yuklaydi"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # API credentials are hardcoded, only load user settings
                    self.target_username = config.get('target_username')
                    self.test_channel_name = config.get('test_channel_name')
                    return True
            except Exception as e:
                logger.error(f"❌ Konfiguratsiya faylini yuklashda xatolik: {e}")
        return False
    
    def save_user_config(self):
        """Foydalanuvchi konfiguratsiyasini saqlaydi"""
        config = {
            # Save user settings only, API credentials are hardcoded
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
        """No key validation needed anymore"""
        return True
    
    async def telegram_verification(self):
        """Telegram hisobni tasdiqlash - faqat kod kiritish"""
        print("\n📱 TELEGRAM HISOBNI TASDIQLASH")
        print("=" * 50)
        print("🔐 API ma'lumotlari: ✅ Yuklangan")
        print("📞 Telefon: ****" + self.phone[-4:])  # Show last 4 digits only
        print("=" * 50)
        
        try:
            session_name = 'sovga_session'
            self.client = TelegramClient(session_name, self.api_id, self.api_hash)
            
            # Clean session if locked
            try:
                await self.client.connect()
            except Exception as session_error:
                if "database is locked" in str(session_error).lower():
                    print("🔒 Sessiya tozalanmoqda...")
                    self.cleanup_session()
                    await asyncio.sleep(1)
                    self.client = TelegramClient(session_name, self.api_id, self.api_hash)
                    await self.client.connect()
            
            # Check if already authorized
            if await self.client.is_user_authorized():
                print("✅ Hisob allaqachon tasdiqlangan!")
                me = await self.client.get_me()
                print(f"👤 Ulanilgan hisob: {me.first_name} {me.last_name or ''}")
                await self.client.disconnect()
                return True
            
            print("⏳ Ulanilmoqda...")
            
            # Start the sign-in process (this will send the code)
            try:
                await self.client.send_code_request(self.phone)
                print("📤 Tasdiqlash kodi yuborildi!")
                print(f"📱 {self.phone} raqamiga kod kelishi kerak")
                print("=" * 30)
                
            except Exception as e:
                print(f"❌ Kod so'rashda xatolik: {e}")
                await self.client.disconnect()
                return False
            
            # Get verification code from user - THIS IS THE MAIN PART
            while True:
                try:
                    print("\n🔢 TASDIQLASH KODI")
                    code = input("📱 Telegram'dan kelgan kodni kiriting: ").strip()
                    
                    if len(code) < 4:
                        print("❌ Kod juda qisqa! Kamida 4 ta raqam kiriting.")
                        continue
                    
                    if not code.isdigit():
                        print("❌ Faqat raqamlarni kiriting!")
                        continue
                    
                    print("⏳ Kod tekshirilmoqda...")
                    await self.client.sign_in(self.phone, code)
                    
                    print("\n🎉 MUVAFFAQIYAT!")
                    print("✅ Hisob muvaffaqiyatli tasdiqlandi!")
                    
                    me = await self.client.get_me()
                    print(f"👤 Ulanilgan hisob: {me.first_name} {me.last_name or ''}")
                    print(f"📞 Telefon: ****{me.phone[-4:] if me.phone else '****'}")
                    
                    await self.client.disconnect()
                    return True
                    
                except PhoneCodeInvalidError:
                    print("\n❌ NOTO'G'RI KOD!")
                    print("💡 Telegram'dan kelgan kodni to'g'ri kiriting")
                    retry = input("Qayta urinib ko'rasizmi? (ha/yo'q): ").strip().lower()
                    if retry not in ['ha', 'yes', 'y', '']:
                        print("❌ Bekor qilindi")
                        await self.client.disconnect()
                        return False
                    continue
                    
                except SessionPasswordNeededError:
                    print("\n🔐 IKKI BOSQICHLI TASDIQLASH")
                    print("Hisobingizda 2FA yoqilgan")
                    
                    while True:
                        password = input("🔐 Ikki bosqichli parolni kiriting: ").strip()
                        if not password:
                            print("❌ Parol bo'sh bo'lmasligi kerak!")
                            continue
                        
                        try:
                            await self.client.sign_in(password=password)
                            print("\n🎉 MUVAFFAQIYAT!")
                            print("✅ Hisob muvaffaqiyatli tasdiqlandi!")
                            
                            me = await self.client.get_me()
                            print(f"👤 Ulanilgan hisob: {me.first_name} {me.last_name or ''}")
                            
                            await self.client.disconnect()
                            return True
                            
                        except Exception as pwd_error:
                            print(f"❌ Parol xato: {pwd_error}")
                            retry = input("Qayta urinib ko'rasizmi? (ha/yo'q): ").strip().lower()
                            if retry not in ['ha', 'yes', 'y', '']:
                                print("❌ Bekor qilindi")
                                await self.client.disconnect()
                                return False
                            continue
                            
                except Exception as e:
                    print(f"❌ Xatolik: {e}")
                    print("📞 Yordam kerak bo'lsa: @unkownles")
                    await self.client.disconnect()
                    return False
                    
        except Exception as e:
            print(f"❌ Umumiy xatolik: {e}")
            print("📞 Yordam uchun: @unkownles")
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
            return False
    
    def get_target_user(self):
        """Kimga xabar yuborishni so'raydi"""
        print("\n👤 XABAR QABUL QILUVCHINI TANLANG")
        print("=" * 40)
        
        # Joriy sozlamani ko'rsatish
        if self.target_username:
            print(f"Joriy: @{self.target_username}")
        
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
    
    async def get_test_channel(self):
        """Test rejimi uchun kanal linkini so'raydi va unga qo'shiladi"""
        print("\n📺 TEST KANALI TANLASH")
        print("=" * 40)
        print("📝 Test uchun kanal linkini kiriting")
        print("💡 Masalan: t.me/example yoki @example")
        
        # Joriy sozlamani ko'rsatish
        if self.test_channel_name:
            print(f"Joriy test kanali: @{self.test_channel_name}")
        
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
                # Try to join the channel
                await self.auto_join_channel(self.test_channel_name, is_test=True)
                return True
    
    async def auto_join_channel(self, channel_name, is_test=False):
        """Kanalga avtomatik qo'shiladi"""
        channel_type = "test" if is_test else "real"
        print(f"\n🔄 {channel_type.upper()} kanalga qo'shilish...")
        
        client = None
        try:
            # Create temporary client for joining
            session_name = 'temp_join_session'
            client = TelegramClient(session_name, self.api_id, self.api_hash)
            await client.start(phone=self.phone)
            
            # Try to find and join the channel
            try:
                # Try different formats
                possible_formats = [
                    channel_name,
                    f"@{channel_name}",
                    f"https://t.me/{channel_name}",
                    f"t.me/{channel_name}"
                ]
                
                channel = None
                for format_name in possible_formats:
                    try:
                        channel = await client.get_entity(format_name)
                        break
                    except:
                        continue
                
                if not channel:
                    print(f"❌ @{channel_name} kanali topilmadi!")
                    return False
                
                # Check if already joined
                try:
                    participants = await client.get_participants(channel, limit=1)
                    print(f"✅ @{channel_name} kanalida allaqachon a'zosiz")
                    return True
                except:
                    # Not joined, try to join
                    pass
                
                # Try to join the channel
                try:
                    await client(functions.channels.JoinChannelRequest(channel))
                    print(f"✅ @{channel_name} kanaliga muvaffaqiyatli qo'shildingiz!")
                    return True
                except Exception as join_error:
                    if "already" in str(join_error).lower():
                        print(f"✅ @{channel_name} kanalida allaqachon a'zosiz")
                        return True
                    elif "private" in str(join_error).lower():
                        print(f"⚠️  @{channel_name} - Bu private kanal. Admin sizni qo'shishi kerak.")
                        print("💡 Kanal adminidan sizni qo'shishini so'rang.")
                        return True  # Continue anyway, user might get added later
                    else:
                        print(f"❌ Kanalga qo'shilishda xatolik: {join_error}")
                        return False
                        
            except Exception as e:
                print(f"❌ Kanal bilan ishlashda xatolik: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Ulanishda xatolik: {e}")
            return False
        finally:
            if client:
                try:
                    await client.disconnect()
                    # Clean up temporary session
                    temp_files = [
                        'temp_join_session.session',
                        'temp_join_session.session-journal'
                    ]
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except:
                                pass
                except:
                    pass
    
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

async def handle_settings():
    """Sozlamalar menyusini boshqaradi"""
    notifier = SovgaXabardorisi()
    notifier.load_user_config()  # Mavjud sozlamalarni yuklash
    
    while True:
        settings_choice = show_settings_menu()
        
        if settings_choice == 1:
            # Telegram Verification
            try:
                result = await notifier.telegram_verification()
                if result:
                    print("✅ Telegram hisob muvaffaqiyatli tasdiqlandi!")
                else:
                    print("❌ Telegram hisobni tasdiqlashda muammo!")
            except Exception as e:
                print(f"❌ Xatolik: {e}")
                print("📞 Yordam uchun: @unkownles")
            
            input("\nDavom etish uchun Enter bosing...")
            
        elif settings_choice == 2:
            # Target Username o'zgartirish
            notifier.get_target_user()
            notifier.save_user_config()
            print("✅ Target username saqlandi!")
            
        elif settings_choice == 3:
            # Test Channel o'zgartirish
            try:
                await notifier.get_test_channel()
                notifier.save_user_config()
                print("✅ Test kanali saqlandi!")
            except Exception as e:
                print(f"❌ Test kanal sozlashda xatolik: {e}")
                print("📞 Yordam uchun: @unkownles")
            
        elif settings_choice == 4:
            # Asosiy menyuga qaytish
            print("🔙 Asosiy menyuga qaytilmoqda...")
            return

async def main():
    """Asosiy funksiya"""
    while True:
        show_banner()
        
        # Mode tanlash
        selected_mode = show_mode_selection()
        
        # Reset rejimi
        if selected_mode == 3:
            if reset_all_data():
                continue
            else:
                continue
        
        # Sozlamalar rejimi
        if selected_mode == 4:
            await handle_settings()
            continue
        
        # Rejimni aniqlash
        mode = 'real' if selected_mode == 1 else 'test'
        
        print(f"\n🎯 Tanlangan rejim: {'REAL MODE' if mode == 'real' else 'TEST MODE'}")
        
        notifier = SovgaXabardorisi(mode=mode)
        
        try:
            # Konfiguratsiya yuklash (API credentials are hardcoded)
            config_loaded = notifier.load_user_config()
            print("✅ API sozlamalari: Avtomatik yuklangan.")
            
            # Target user tekshirish
            if not notifier.target_username:
                print("❌ Target username sozlanmagan!")
                print("💡 4-Settings → 2-Target Username menusidan sozlang.")
                continue
            
            # Test rejimi uchun test kanali tekshirish
            if mode == 'test' and not notifier.test_channel_name:
                print("❌ Test kanali sozlanmagan!")
                print("💡 4-Settings → 3-Test Channel menusidan sozlang.")
                continue
            
            print("✅ Barcha sozlamalar tayyor.")
            
            # Ulanish
            print("\n🔌 Ulanilmoqda...")
            if not await notifier.initialize_client():
                continue
            
            # Test
            print("\n🧪 Test...")
            if not await notifier.test_connection():
                continue
            
            # Kuzatuvni boshlash
            mode_name = "REAL REJIMI" if mode == 'real' else "TEST REJIMI"
            print(f"\n🚀 {mode_name} boshlandi...")
            await notifier.start_monitoring()
            
            # Bot to'xtagandan so'ng asosiy menyuga qaytish
            break
            
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}")
            print("📞 Xatoliklar uchun: @unkownles yoki admin bilan bog'laning")
            input("Davom etish uchun Enter ni bosing...")
            continue
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