const allCommands = [
{name:"/give",desc:"O‘yinchiga buyum beradi.",code:"/give @s diamond 64"},
{name:"/tp",desc:"O‘yinchini teleport qiladi.",code:"/tp @s 100 70 100"},
{name:"/teleport",desc:"O‘yinchini boshqa joyga teleport qiladi.",code:"/teleport @s 0 80 0"},
{name:"/time",desc:"Vaqtni o‘zgartiradi.",code:"/time set day"},
{name:"/weather",desc:"Ob-havoni o‘zgartiradi.",code:"/weather clear"},
{name:"/gamemode",desc:"O‘yin rejimini o‘zgartiradi.",code:"/gamemode creative"},
{name:"/difficulty",desc:"Qiyinchilik darajasini o‘zgartiradi.",code:"/difficulty peaceful"},
{name:"/effect",desc:"Effekt beradi.",code:"/effect @s speed 60 2"},
{name:"/summon",desc:"Mob yoki obyekt chaqiradi.",code:"/summon zombie"},
{name:"/kill",desc:"Tanlangan obyektni yo‘q qiladi.",code:"/kill @e[type=zombie]"},
{name:"/clear",desc:"Inventarni tozalaydi.",code:"/clear @s"},
{name:"/setblock",desc:"Belgilangan joyga blok qo‘yadi.",code:"/setblock ~ ~ ~ diamond_block"},
{name:"/fill",desc:"Hududni bloklar bilan to‘ldiradi.",code:"/fill ~-5 ~-1 ~-5 ~5 ~-1 ~5 stone"},
{name:"/clone",desc:"Bir hududni boshqa joyga nusxalaydi.",code:"/clone 0 60 0 10 70 10 20 60 20"},
{name:"/locate",desc:"Yaqin tuzilmani topadi.",code:"/locate structure village"},
{name:"/spawnpoint",desc:"O‘yinchining spawn nuqtasini belgilaydi.",code:"/spawnpoint @s"},
{name:"/setworldspawn",desc:"Dunyoning spawn nuqtasini belgilaydi.",code:"/setworldspawn ~ ~ ~"},
{name:"/xp",desc:"Tajriba beradi.",code:"/xp 10L @s"},
{name:"/experience",desc:"Tajriba miqdorini boshqaradi.",code:"/experience add @s 10 levels"},
{name:"/title",desc:"Ekranga katta yozuv chiqaradi.",code:"/title @a title Salom!"},
{name:"/say",desc:"Chatga xabar chiqaradi.",code:"/say Salom, Minecraft!"},
{name:"/msg",desc:"O‘yinchiga shaxsiy xabar yuboradi.",code:"/msg @p Salom!"},
{name:"/playsound",desc:"Ovoz ijro etadi.",code:"/playsound random.orb @s"},
{name:"/particle",desc:"Particle effekt chiqaradi.",code:"/particle minecraft:heart ~ ~1 ~"},
{name:"/enchant",desc:"Buyumni sehrlaydi.",code:"/enchant @s sharpness 5"},
{name:"/recipe",desc:"Retseptni ochadi yoki yopadi.",code:"/recipe give @s *"},
{name:"/difficulty",desc:"Dunyo qiyinligini belgilaydi.",code:"/difficulty hard"},
{name:"/gamerule",desc:"Dunyo qoidasini o‘zgartiradi.",code:"/gamerule keepInventory true"},
{name:"/seed",desc:"Dunyo urug‘ini ko‘rsatadi.",code:"/seed"},
{name:"/list",desc:"Serverdagi o‘yinchilarni ko‘rsatadi.",code:"/list"},
{name:"/me",desc:"Harakat haqida xabar chiqaradi.",code:"/me kuldi"},
{name:"/tag",desc:"O‘yinchiga tag qo‘shadi.",code:"/tag @s add builder"},
{name:"/team",desc:"Jamoalarni boshqaradi.",code:"/team add red"},
{name:"/execute",desc:"Buyruqni boshqa obyekt nomidan bajaradi.",code:"/execute as @a run say Salom"},
{name:"/scoreboard",desc:"Scoreboard tizimini boshqaradi.",code:"/scoreboard objectives list"},
{name:"/reload",desc:"Funksiya va ma’lumotlarni qayta yuklaydi.",code:"/reload"},
{name:"/stop",desc:"Serverni to‘xtatadi.",code:"/stop"},
{name:"/op",desc:"O‘yinchiga operator huquqini beradi.",code:"/op Player"},
{name:"/deop",desc:"Operator huquqini olib tashlaydi.",code:"/deop Player"},
{name:"/kick",desc:"O‘yinchini serverdan chiqaradi.",code:"/kick Player"},
{name:"/ban",desc:"O‘yinchini serverdan bloklaydi.",code:"/ban Player"}
];

function commands(){
    openModal("🧩 Buyruqlar",`
        <input class="search" id="allCommandSearch"
        placeholder="Buyruq qidiring..." oninput="searchAllCommands()">
        <div id="allCommandsList"></div>
    `);
    searchAllCommands();
}

function searchAllCommands(){
    const q=(document.getElementById("allCommandSearch")?.value||"").toLowerCase();
    const list=allCommands.filter(x=>
        x.name.toLowerCase().includes(q) ||
        x.desc.toLowerCase().includes(q)
    );
    document.getElementById("allCommandsList").innerHTML=list.map(x=>`
        <div class="result">
            <div class="result-title">${x.name}</div>
            <div class="result-desc">${x.desc}</div>
            <div class="code">${x.code}</div>
        </div>
    `).join("");
}

function recipes(){
    openModal("🛠️ Retseptlar",`
        <input class="search" placeholder="Retsept qidiring..."
        oninput="filterRecipes(this.value)">
        <div id="recipeList"></div>
    `);
    filterRecipes("");
}

const recipeData=[
["💎 Olmos qilichi","2 ta olmos + 1 ta tayoq","💎 | 💎 | ⬜<br>⬜ | 🪵 | ⬜<br>⬜ | 🪵 | ⬜"],
["⚔️ Temir qilich","2 ta temir + 1 ta tayoq","⛓️ | ⛓️ | ⬜<br>⬜ | 🪵 | ⬜<br>⬜ | 🪵 | ⬜"],
["⛏️ Olmos qazig‘ich","3 ta olmos + 2 ta tayoq","💎 | 💎 | 💎<br>⬜ | 🪵 | ⬜<br>⬜ | 🪵 | ⬜"],
["🛡️ Qalqon","6 ta taxta + 1 ta temir","🪵 | 🪵 | 🪵<br>🪵 | ⛓️ | 🪵<br>⬜ | 🪵 | ⬜"],
["🕯️ Mash’ala","1 ta ko‘mir + 1 ta tayoq","⬜ | ⚫<br>⬜ | 🪵"],
["📦 Sandıq","8 ta taxta","🪵 | 🪵 | 🪵<br>🪵 | ⬜ | 🪵<br>🪵 | 🪵 | 🪵"],
["🪜 Narvon","7 ta tayoq","🪵 | ⬜ | 🪵<br>🪵 | 🪵 | 🪵<br>🪵 | ⬜ | 🪵"],
["🧪 Pech","8 ta tosh","🪨 | 🪨 | 🪨<br>🪨 | ⬜ | 🪨<br>🪨 | 🪨 | 🪨"],
["🧱 Qurilish stoli","4 ta taxta","🪵 | 🪵<br>🪵 | 🪵"],
["🪣 Chelak","3 ta temir","⛓️ | ⬜ | ⛓️<br>⬜ | ⛓️ | ⬜"]
];

function filterRecipes(q){
    q=q.toLowerCase();
    document.getElementById("recipeList").innerHTML=
    recipeData.filter(x=>x[0].toLowerCase().includes(q))
    .map(x=>`
        <div class="result">
            <div class="result-title">${x[0]}</div>
            <div class="result-desc">${x[1]}</div>
            <div class="code">${x[2]}</div>
        </div>
    `).join("");
}

function tools(){
    openModal("🧰 Foydali vositalar",`
        <div class="result">
            <div class="result-title">📍 Koordinatalar</div>
            <div class="result-desc">Joylashuvingizni aniqlash va qurilish joyini belgilashda yordam beradi.</div>
            <div class="code">X: 100  Y: 70  Z: 100</div>
        </div>
        <div class="result">
            <div class="result-title">🧭 Kompas</div>
            <div class="result-desc">Spawn nuqtasiga yo‘nalishni aniqlash uchun ishlatiladi.</div>
        </div>
        <div class="result">
            <div class="result-title">🕯️ Yorug‘lik</div>
            <div class="result-desc">Qorong‘i joylarni yoritish uchun mash’ala va boshqa yorug‘lik manbalaridan foydalaning.</div>
        </div>
        <div class="result">
            <div class="result-title">🗺️ Xarita</div>
            <div class="result-desc">Hududlarni o‘rganish va yo‘nalishni topishda yordam beradi.</div>
        </div>
    `);
}

function profile(){
    openModal("👤 Profil",`
        <div class="result">
            <div class="result-title">🎮 Minecraft yordamchisi</div>
            <div class="result-desc">Siz bu yerda Minecraft buyruqlari, retseptlar va foydali ma’lumotlardan foydalanishingiz mumkin.</div>
        </div>
        <div class="result">
            <div class="result-title">🧩 Buyruqlar</div>
            <div class="result-desc">${allCommands.length} ta buyruq mavjud.</div>
        </div>
        <div class="result">
            <div class="result-title">🛠️ Retseptlar</div>
            <div class="result-desc">${recipeData.length} ta retsept mavjud.</div>
        </div>
    `);
}

function settings(){
    openModal("⚙️ Sozlamalar",`
        <div class="result">
            <div class="result-title">🌐 Til</div>
            <div class="result-desc">O‘zbek tili</div>
        </div>
        <div class="result">
            <div class="result-title">🎨 Ko‘rinish</div>
            <div class="result-desc">Telegram mavzusiga moslashtirilgan.</div>
        </div>
        <div class="result">
            <div class="result-title">📱 Web App</div>
            <div class="result-desc">Minecraft yordamchisi faol.</div>
        </div>
    `);
}
