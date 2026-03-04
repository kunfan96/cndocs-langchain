/**
 * 弹框显示脚本
 * 功能：每天第1/5/7/10次打开页面会弹出一个弹框，显示图片
 */

function initPopupModal() {
  // 获取今天的日期作为key
  const today = new Date().toDateString();
  const storageKey = `popup_visits_${today}`;

  // 获取今天的访问次数
  let visits = parseInt(localStorage.getItem(storageKey)) || 0;
  visits++;

  // 更新localStorage
  localStorage.setItem(storageKey, visits);

  // 触发显示弹框的次数，可以根据需要调整
  const triggerTimes = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50];

  if (triggerTimes.includes(visits)) {
    showPopupModal();
  }
}

function showPopupModal() {
  // 检查弹框是否已存在
  if (document.getElementById("popup-modal-overlay")) {
    return;
  }

  // 创建遮罩层
  const overlay = document.createElement("div");
  overlay.id = "popup-modal-overlay";
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
  `;

  // 创建弹框容器
  const modal = document.createElement("div");
  modal.id = "popup-modal-container";
  modal.style.cssText = `
    position: relative;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    max-width: 500px;
    width: 90%;
    padding: 20px;
    animation: popupSlideIn 0.3s ease-out;
  `;

  // 创建关闭按钮
  const closeBtn = document.createElement("button");
  closeBtn.id = "popup-modal-close";
  closeBtn.innerHTML = "&times;";
  closeBtn.style.cssText = `
    position: absolute;
    top: 10px;
    right: 10px;
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: #999;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s;
  `;

  closeBtn.addEventListener("mouseenter", function () {
    this.style.color = "#333";
  });

  closeBtn.addEventListener("mouseleave", function () {
    this.style.color = "#999";
  });

  closeBtn.addEventListener("click", function () {
    closePopupModal();
  });

  // 创建图片容器
  const imageContainer = document.createElement("div");
  imageContainer.style.cssText = `
    text-align: center;
    margin-top: 10px;
  `;

  // 创建图片
  const img = document.createElement("img");
  img.src = "https://kunfanyang.site/site-file/wx_code.jpg";
  img.alt = "WeChat QR Code";
  img.style.cssText = `
    max-width: 100%;
    height: auto;
    border-radius: 4px;
  `;

  img.addEventListener("error", function () {
    img.style.display = "none";
    const errorMsg = document.createElement("p");
    errorMsg.textContent = "图片加载失败";
    errorMsg.style.color = "#999";
    imageContainer.appendChild(errorMsg);
  });

  imageContainer.appendChild(img);

  // 组装弹框
  modal.appendChild(closeBtn);
  modal.appendChild(imageContainer);
  overlay.appendChild(modal);

  // 添加到页面
  document.body.appendChild(overlay);

  // 点击遮罩层关闭弹框
  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) {
      closePopupModal();
    }
  });

  // 添加CSS动画
  addPopupAnimation();
}

function closePopupModal() {
  const overlay = document.getElementById("popup-modal-overlay");
  if (overlay) {
    overlay.style.animation = "popupSlideOut 0.3s ease-out";
    setTimeout(function () {
      overlay.remove();
    }, 300);
  }
}

function addPopupAnimation() {
  // 检查动画样式是否已添加
  if (document.getElementById("popup-modal-styles")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "popup-modal-styles";
  style.textContent = `
    @keyframes popupSlideIn {
      from {
        opacity: 0;
        transform: scale(0.9);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }
    
    @keyframes popupSlideOut {
      from {
        opacity: 1;
        transform: scale(1);
      }
      to {
        opacity: 0;
        transform: scale(0.9);
      }
    }
  `;
  document.head.appendChild(style);
}

// 页面加载完成后初始化
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPopupModal);
} else {
  initPopupModal();
}
