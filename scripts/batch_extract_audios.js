/**
 * 批量提取微信文章音频信息的浏览器脚本
 * 在Chrome控制台运行此脚本
 */

// 64篇文章的链接列表
const articles = [
  {"index":1,"title":"课本和朗读2024秋：P1外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=3&sn=c0e42ba3822c12f41b36b46b92482830&chksm=eb9c41e9dcebc8fff4c91ad6a8905e92fc4795bd35aed771ecbbae5c976cfbb4dd269cb0ef68#rd"},
  {"index":2,"title":"课本和朗读2024秋：P2外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=2&sn=203f63dba855b8bacf189b21e3b09273&chksm=eb9c41e9dcebc8ff9c2261f6529e73e9f9b6e8f16f471ed8fa3b7e13cd2c7df89ec1eddf8e9c#rd"},
  {"index":3,"title":"课本和朗读2024秋：P3外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247539989&idx=1&sn=0e7a887cd9ab540c42bfc822d3c1d513&chksm=eb9c41e9dcebc8ff440a7e53269f8cc0f669f8ad6d19d3b4b98fd41d7c8b27392bc5367e0fff#rd"},
  {"index":4,"title":"课本和朗读2024秋：P4外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=4&sn=aba3d6ccd9f9789c6df745e06e2b9901&chksm=eb9c41a7dcebc8b176f9fa1a22e5f062f7085eb488fa253effe4beabfdb1869cca6d99f32072#rd"},
  {"index":5,"title":"课本和朗读2024秋：P5外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=3&sn=0a09e213315f3ac83bf83114b10da870&chksm=eb9c41a7dcebc8b14236068d125469e56408944ef342a63110426e523f1dc71c20967e75068b#rd"},
  {"index":6,"title":"课本和朗读2024秋：P6外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=2&sn=96e00be7677b71f20ddd4cc1aeca7cd7&chksm=eb9c41a7dcebc8b163bcb938f0fefe8f7e0c3783531d95d1131fad8f647545fbd624b58179ee#rd"},
  {"index":7,"title":"课本和朗读2024秋：P62Unit 1外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540059&idx=1&sn=0dafd721b74fbeef38888b6900e0d990&chksm=eb9c41a7dcebc8b10937ad46af92ceba6b80d524eda8fa8317bda5ead33d6fe3fc621b9ba58c#rd"},
  {"index":8,"title":"课本和朗读2024秋：P7外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=7&sn=9c7eaab1b0c372a494952cf0421faebd&chksm=eb9c4144dcebc852811e1237dd59fa68e2685926d3ecbaa390a38630777e9bcd37f7564dc792#rd"},
  {"index":9,"title":"课本和朗读2024秋：P8外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=6&sn=8ae2a0540ae14dd7c9cb2ad94807a79a&chksm=eb9c4144dcebc85233c0e88964d4cdc6ba0bd9c82135afc9bd073589de95a9a2f83aeb2658fb#rd"},
  {"index":10,"title":"课本和朗读2024秋：P9外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=5&sn=da748575e95b87938075b888dd8d5637&chksm=eb9c4144dcebc8527bf1fb13bdd02fe04e5f542940fe0906f5607d88ffdaaab1bb05e9e5123f#rd"},
];

// 提取当前页面音频的函数
function extractCurrentPageAudios() {
  const audios = document.querySelectorAll('mp-common-mpaudio');
  const audioData = [];
  audios.forEach((audio, idx) => {
    const fileId = audio.getAttribute('voice_encode_fileid');
    audioData.push({
      index: idx + 1,
      name: audio.getAttribute('name'),
      fileId: fileId,
      playLength: audio.getAttribute('play_length'),
      author: audio.getAttribute('author'),
      downloadUrl: `https://res.wx.qq.com/voice/getvoice?mediaid=${fileId}`
    });
  });
  return audioData;
}

// 当前页面的文章索引（从1开始）
let currentArticleIndex = 1;

// 存储所有文章的音频信息
const allAudios = {};

// 处理当前页面
function processCurrentPage() {
  const article = articles[currentArticleIndex - 1];
  const audios = extractCurrentPageAudios();

  allAudios[article.index] = {
    title: article.title,
    audios: audios
  };

  console.log(`[${article.index}/10] ${article.title}`);
  console.log(`  找到 ${audios.length} 个音频`);

  audios.forEach(a => {
    console.log(`  - ${a.name}: ${a.downloadUrl}`);
  });

  // 前往下一篇文章
  currentArticleIndex++;
  if (currentArticleIndex <= articles.length) {
    const nextArticle = articles[currentArticleIndex - 1];
    console.log(`\n3秒后跳转到下一篇文章...`);
    setTimeout(() => {
      window.location.href = nextArticle.link;
    }, 3000);
  } else {
    console.log('\n========================================');
    console.log('所有文章处理完成！');
    console.log('========================================');
    console.log(JSON.stringify(allAudios, null, 2));

    // 下载为JSON文件
    const blob = new Blob([JSON.stringify(allAudios, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audio_list.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

// 启动处理
console.log('开始提取音频信息...');
processCurrentPage();
