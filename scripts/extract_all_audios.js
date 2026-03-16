/**
 * 批量提取所有64篇文章的音频信息
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
  {"index":11,"title":"课本和朗读2024秋：P10外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=4&sn=80e4bf0abf81575e6485254b318f5b09&chksm=eb9c4144dcebc8528fc14966970517fa1e6f755f2ad4cd7802fab797cb183488c18b03fce9b8#rd"},
  {"index":12,"title":"课本和朗读2024秋：P11外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=3&sn=b5a07fe12336abc6ec73d84737811f81&chksm=eb9c4144dcebc852ec389cc4f9e66c6f0b87357c6f4ec3b4e3fd03295e7b38b4320ccefd00d9#rd"},
  {"index":13,"title":"课本和朗读2024秋：P12外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=2&sn=50a7e8e507ccd46d6e7359923db4a792&chksm=eb9c4144dcebc852dc0546f882b6d2eb7e385a8a8f205b31a186b0f420f8fdcc41846dc6ae3b#rd"},
  {"index":14,"title":"课本和朗读2024秋：P62Unit 2外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540152&idx=1&sn=2cdbdfa4eca8c308a0d2c8f4705a23a9&chksm=eb9c4144dcebc852a31a4fbe3e80d41f37c410f95d19bdd248259678bfe18346a3c6a7ab50eb#rd"},
  {"index":15,"title":"课本和朗读2024秋：P13外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=7&sn=bb1e0b7768c64248d87fe1814f4c4cf8&chksm=eb9c4143dcebc855408874b1643c550aed30ffce804ad17ac5650eb63380933722542124df59#rd"},
  {"index":16,"title":"课本和朗读2024秋：P14外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=6&sn=04b78f342e1e93fef7d4cecb39f06148&chksm=eb9c4143dcebc855fbed9cfa4afbf00892d499473c7b21b444b45a5736b1a8b5f4efa4f43ff9#rd"},
  {"index":17,"title":"课本和朗读2024秋：P15外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=5&sn=af00390c4df45897843153bf0c10ee3f&chksm=eb9c4143dcebc85552db06b87abe6291681a4a4d0e8ae3b3d7ff28eeb3c3a31031c27844ea50#rd"},
  {"index":18,"title":"课本和朗读2024秋：P16外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=4&sn=c34721a184f4280d2e549232b72ce934&chksm=eb9c4143dcebc8555f31d5a4a35ea8bca9f6112056ef5cb49d4e8bccfa9d1833eb71f54dc536#rd"},
  {"index":19,"title":"课本和朗读2024秋：P17外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=3&sn=fbcc702576771a2294fb056839f7fb90&chksm=eb9c4143dcebc85581daa9422a79da92d431535b8a99cbbe9a04e54019a78b3460d5d4b4ec7f#rd"},
  {"index":20,"title":"课本和朗读2024秋：P18外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=2&sn=ffae2b82530f8fe2ca0e7810974a45fa&chksm=eb9c4143dcebc855b90039bd95670e1c77b9c625f3a466421e2235fe166d6eab4326dd88c978#rd"},
  {"index":21,"title":"课本和朗读2024秋：P62-63Unit 3外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540159&idx=1&sn=69ee1ba08e58caf3a7c102ec39388e41&chksm=eb9c4143dcebc855b33b8585d7c46a2afc8a186fbc095f28e6eb749a027f8dee26219eecd583#rd"},
  {"index":22,"title":"课本和朗读2024秋：P19外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=7&sn=4753e1b14daf31a444d733e0c77dddf6&chksm=eb9c413bdcebc82d8fd127460dc869e65aa89197e6c79fd40c535aec8c71f78446ab33b89880#rd"},
  {"index":23,"title":"课本和朗读2024秋：P20外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=6&sn=e2cb1d4fbb59e3b27c8660ca45286cd3&chksm=eb9c413bdcebc82d6023992dbdd6be7a6015bfb615f3455d817b0edda9f4232bc9580a07ac69#rd"},
  {"index":24,"title":"课本和朗读2024秋：P21外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=5&sn=6c67a8634ea7aaae129768fed8d19672&chksm=eb9c413bdcebc82d2c4a129ce0f3c0064867c19f66de0b4ba5c8f0e055ba0374a5d4e2572c48#rd"},
  {"index":25,"title":"课本和朗读2024秋：P22外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=4&sn=c46d84c3844299c7bf8f7790974c83f0&chksm=eb9c413bdcebc82d2765a0821eec9c0bd851dc390123194985ae5be2e72319a42b454c2b2a3e#rd"},
  {"index":26,"title":"课本和朗读2024秋：P23外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=3&sn=ad9c32689316d5cb78988d55c5707efe&chksm=eb9c413bdcebc82d18e0aaf996f88d1429bcd05fdfbabb48071bc1516ac08628ebd9158221cc#rd"},
  {"index":27,"title":"课本和朗读2024秋：P24外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=2&sn=28cfc5232cf880ef9c27bb03af5389d9&chksm=eb9c413bdcebc82dfb8ad0d4d53325089ef852732771e66481b1c2feee625fd437d32e78dc9c#rd"},
  {"index":28,"title":"课本和朗读2024秋：P63Unit 4外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540167&idx=1&sn=faa7b8427ad44c83486b3345df6143c3&chksm=eb9c413bdcebc82dce453e053cc1a39fc856707c0999148be48d1023df29ba5ac7357f5e4038#rd"},
  {"index":29,"title":"课本和朗读2024秋：P25外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=7&sn=38e2cf72b16d71272d21973dbf4d9fd5&chksm=eb9c410bdcebc81dc18537b1d77dabafd8e7eda6837092d774a77c842f405c8b6fef40af33fc#rd"},
  {"index":30,"title":"课本和朗读2024秋：P26外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=6&sn=6e715a31123a63702ca45447c5f0a396&chksm=eb9c410bdcebc81d83667bd10833ce6ec76937cb26b6c4fe250cded1557058f600c7a065e3a4#rd"},
  {"index":31,"title":"课本和朗读2024秋：P27外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=5&sn=c520fe2d44e3ea5e5264606e0bbbe6fa&chksm=eb9c410bdcebc81dc41c904ad187cbbe4e30460500eb8684a73f544a0d0f24d5d66f039e084b#rd"},
  {"index":32,"title":"课本和朗读2024秋：P28外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=4&sn=d86d1fc5f759bde1aa96b70b4692081b&chksm=eb9c410bdcebc81d2172ae0b23d03a33197c9714483bc0604e1dc305e19b1527a2896f1da4ad#rd"},
  {"index":33,"title":"课本和朗读2024秋：P29外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=3&sn=c9cdbb1815598de513ec9da2b2dceff7&chksm=eb9c410bdcebc81d4b5eaba68cd25ba8293ae4de19c2822b7f9c97a42cee02f8abc1df5fbac2#rd"},
  {"index":34,"title":"课本和朗读2024秋：P30外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=2&sn=e1d84dc4d7c48ef0ed86c6d24298dee0&chksm=eb9c410bdcebc81d1558aa824a72c4cd93e5aa62800202b444219d18df50619c5d7f40ac9a32#rd"},
  {"index":35,"title":"课本和朗读2024秋：P63Unit 5外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540215&idx=1&sn=635e16e85cf74cff960851789a2b14c7&chksm=eb9c410bdcebc81d88a9ecb27db8fc6c895f62cf69054676fc565d0a946c36d680c74fe2f1d8#rd"},
  {"index":36,"title":"课本和朗读2024秋：P31外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=7&sn=e2c529d46ab1de1e0a5bbac3b0c74414&chksm=eb9c426edcebcb7866da835fe0624525357bcb45b7ceafd5b7e138fa6ce88b8ef306dd3d56eb#rd"},
  {"index":37,"title":"课本和朗读2024秋：P32外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=6&sn=51f5e60fd1a16dbfd044fc6e871ff083&chksm=eb9c426edcebcb7832c9b01f3bb6525a7c765854dead1b850145e13994f2e5f1a48108a2f793#rd"},
  {"index":38,"title":"课本和朗读2024秋：P33外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=5&sn=720b9f36ae6ec4c526f18c6dab37620b&chksm=eb9c426edcebcb7821da971a7fe6a239f4fa59d1c9d623d485c01465e9fe689bf0337f34ac2f#rd"},
  {"index":39,"title":"课本和朗读2024秋：P34外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=4&sn=8d409a65b41c93e9c31e473d215276aa&chksm=eb9c426edcebcb78b4d882d64f4155827fa1033e5c1781c717b34c5156a930306579e242504d#rd"},
  {"index":40,"title":"课本和朗读2024秋：P35外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=3&sn=8f63add0625ef1ccacfb87740845dcc2&chksm=eb9c426edcebcb786444bd4775a85150119135072ace440eb6ba0bddd759a75351e345f3f6cd#rd"},
  {"index":41,"title":"课本和朗读2024秋：P36外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=2&sn=9c0d340c12ce6b3ecf6219d00af5d703&chksm=eb9c426edcebcb78b1dc44ea286a22fab7166005f3292159409c77c83c3ffc982acdfbaf044b#rd"},
  {"index":42,"title":"课本和朗读2024秋：P63-64Unit 6外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540370&idx=1&sn=00e89c776c72360fccd95917d7acdc8f&chksm=eb9c426edcebcb783b912073c0d948d38e22f7e93ab51d77fa08126ed6f6718234533fb36e79#rd"},
  {"index":43,"title":"课本和朗读2024秋：P37外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540372&idx=5&sn=897fb1e2105cb5605988d15e162aa887&chksm=eb9c4268dcebcb7ef27e1063e38c0e5beb07836c91ccbd1ad442b97ddfe73cc731e037ad47af#rd"},
  {"index":44,"title":"课本和朗读2024秋：P38外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540372&idx=4&sn=fae56640d74937df00ccd652357cfa08&chksm=eb9c4268dcebcb7ecae4b9d21508fe5d3ef5fc46ba09c601f0bcb460456031098c2bb02afef1#rd"},
  {"index":45,"title":"课本和朗读2024秋：P39外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540372&idx=3&sn=8e6596a9cd33ec2c68d045db21721c1a&chksm=eb9c4268dcebcb7e4e4dbf47d4eeef357cd72452befe9a8eb43422a0db33cc74cd4bdc7b6832#rd"},
  {"index":46,"title":"课本和朗读2024秋：P40外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540372&idx=2&sn=3f6ca9c4f88524b144e60d2eaf955629&chksm=eb9c4268dcebcb7ec046996e0dbd9d84c2d30260b4d865d6419c8e108b13b95981eab948a5d4#rd"},
  {"index":47,"title":"课本和朗读2024秋：P41外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540372&idx=1&sn=18da9becd09e4f99c3a0e9336e64bbe4&chksm=eb9c4268dcebcb7e819941f6bfc6a19ac56426f0f2c5045832b013b5d465a0f6f3b9178dd6a5#rd"},
  {"index":48,"title":"课本和朗读2024秋：P42外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=8&sn=fd6f081ee3952c5a099fd60799b39ae1&chksm=eb9c4266dcebcb700be58d5ee6cdc86b53ec98d2e3e4f48bbc829eb57d03313c70d276ff9d3f#rd"},
  {"index":49,"title":"课本和朗读2024秋：P43外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=7&sn=99581ef0e302fb356ec01f0f3483468c&chksm=eb9c4266dcebcb70ae7b9d3660a9c85574a3cc3fbeaa73b1494f48cd30e1ab4d72e8f2081037#rd"},
  {"index":50,"title":"课本和朗读2024秋：P44外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=6&sn=2e8d99aee5e28bb81ee69d7757d3a394&chksm=eb9c4266dcebcb70f7df52d941c5ae1ebb078862ea7747ef749033d8946d1cd538ca5a91b04c#rd"},
  {"index":51,"title":"课本和朗读2024秋：P45外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=5&sn=fb6f034daeec16a67816f6079841cd04&chksm=eb9c4266dcebcb70c9aa761819e7ad9204a43714db27ca2ec1dd64d09dabd92b53af75a6a343#rd"},
  {"index":52,"title":"课本和朗读2024秋：P46外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=4&sn=7f21bf6b51e9f6331b5479188cb310b9&chksm=eb9c4266dcebcb705d4c8695032de5b1b13429772c3ccfc46e15fc268fbd0548ae67441b7212#rd"},
  {"index":53,"title":"课本和朗读2024秋：P47外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=3&sn=b66e487f24cbe1462c449cad90acaf92&chksm=eb9c4266dcebcb70739540bfc6adaf2c47d1732af79a7ecc7659f9b0ce3f0342017f5ae2031b#rd"},
  {"index":54,"title":"课本和朗读2024秋：P48外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=2&sn=0f2072b19ee9fa41b870e2f08581254d&chksm=eb9c4266dcebcb70877005800c6bfb7bee1c50cd1225367148316cbadcb70c7938411043739b#rd"},
  {"index":55,"title":"课本和朗读2024秋：P49外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540378&idx=1&sn=e94fd4c28ab6d660d62a0dd59a728523&chksm=eb9c4266dcebcb700011dcb4f20a6f42070a0e74d4ae2bcac960879d39189ba18c6cc3e577aa#rd"},
  {"index":56,"title":"课本和朗读2024秋：P50外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=8&sn=948e31fe09c9bf52390ff87f07d477f2&chksm=eb9c425fdcebcb49d0ed6ac1735abf872cd016768fc56344676e2516eb6126d457ac4d4c39c7#rd"},
  {"index":57,"title":"课本和朗读2024秋：P51外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=7&sn=c5a5cd61a23f997c90c7fe61c10c472f&chksm=eb9c425fdcebcb498f472ddce1d655bf62305d77ee9866db5cc0a1c749526c74b827b28f35fd#rd"},
  {"index":58,"title":"课本和朗读2024秋：P52外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=6&sn=8371bf46bce93cc0942040b2e16721f9&chksm=eb9c425fdcebcb49e75eeefd364627df536b0c14f35a45c8b995ed86a78d4db2b56b646be439#rd"},
  {"index":59,"title":"课本和朗读2024秋：P53外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=5&sn=db06e8792422fbeafdeb657c3747e434&chksm=eb9c425fdcebcb49003e61320ff7f369442cd4a318bf6f5f5313a17d5492737c741458b32963#rd"},
  {"index":60,"title":"课本和朗读2024秋：P54-57外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=4&sn=3baa97b6e3a701f603759d42ecca4f1d&chksm=eb9c425fdcebcb49d231dd0f354b9b467da2bf805e15a598d7680ecaf7a085934f6fc4cf668f#rd"},
  {"index":61,"title":"课本和朗读2024秋：P58-61外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=3&sn=f03ea8b459fbde74e182e1dab1d5f058&chksm=eb9c425fdcebcb4954631fd35324cc339050c571fc71bfd42f49935c67fbe1c693506241c811#rd"},
  {"index":62,"title":"课本和朗读2024秋：P65-67外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=2&sn=7a5fd8468f0a3d5567bd5562ddfd350d&chksm=eb9c425fdcebcb49097d2b51b6f987007eb42f13b507370241e4f48d523e35934b3468be11d5#rd"},
  {"index":63,"title":"课本和朗读2024秋：P68外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540387&idx=1&sn=f43597a5d25870ef4c70799875abf343&chksm=eb9c425fdcebcb49c81ff184e97e1bb9eec57ad27c2f325177e065c4c9ec3c67d51f93ecb3fa#rd"},
  {"index":64,"title":"课本和朗读2024秋：P69,71,73,75外研新交际英语一年级上册","link":"http://mp.weixin.qq.com/s?__biz=MzI4MjE1MjMzOQ==&mid=2247540389&idx=1&sn=075a63d57d653c0c9f00617e88ad6d8a&chksm=eb9c4259dcebcb4fb354b4f1a31576c423098b3c390dbc53a71bb75f7d345042a68c60f0820a#rd"},
];

// 存储所有文章的音频信息
const allAudios = {};
let currentArticleIndex = 1;

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

// 处理当前页面
async function processCurrentPage() {
  const article = articles[currentArticleIndex - 1];
  const audios = extractCurrentPageAudios();

  allAudios[article.index] = {
    title: article.title,
    link: article.link,
    audioCount: audios.length,
    audios: audios
  };

  console.log(`[${article.index}/64] ${article.title} - ${audios.length}个音频`);

  // 显示每个音频
  audios.forEach(a => {
    console.log(`  ${a.index}. ${a.name} (${a.playLength}ms)`);
  });

  // 前往下一篇文章
  currentArticleIndex++;
  if (currentArticleIndex <= articles.length) {
    const nextArticle = articles[currentArticleIndex - 1];
    console.log(`等待3秒后跳转到下一篇...`);
    await new Promise(r => setTimeout(r, 3000));
    window.location.href = nextArticle.link;
  } else {
    console.log('\n========================================');
    console.log('所有64篇文章处理完成！');
    console.log('========================================');

    // 统计
    let totalAudios = 0;
    Object.values(allAudios).forEach(a => totalAudios += a.audioCount);
    console.log(`总计音频数: ${totalAudios}`);

    // 输出完整JSON
    console.log('\n完整数据:');
    console.log(JSON.stringify(allAudios, null, 2));

    // 下载为JSON文件
    const blob = new Blob([JSON.stringify(allAudios, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'all_audios_64.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    console.log('\n已下载 all_audios_64.json');
  }
}

// 启动处理
console.log('开始批量提取64篇文章的音频...');
console.log('注意: 脚本会自动遍历所有文章，请保持浏览器打开');
processCurrentPage();
