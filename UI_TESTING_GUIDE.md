# AstraVerify UI Testing Guide

## 🎯 **Testing Overview**

This guide provides comprehensive testing procedures for AstraVerify across different device sizes and scenarios.

## 📱 **Device Testing Matrix**

### **1. Mobile (Phone) Testing**
- **Devices**: iPhone 12, Samsung Galaxy, Google Pixel
- **Viewport**: 390x844px
- **Browser**: Chrome DevTools, Safari (iOS)

### **2. Tablet Testing**
- **Devices**: iPad Pro, Samsung Galaxy Tab
- **Viewport**: 1024x1366px
- **Browser**: Safari (iPad), Chrome

### **3. Desktop Testing**
- **Devices**: MacBook, Windows PC
- **Viewport**: 1920x1080px
- **Browser**: Chrome, Firefox, Safari

## 🧪 **Manual Testing Checklist**

### **✅ Initial Page Load**
- [ ] Page loads without errors
- [ ] Header displays "AstraVerify"
- [ ] Input field is visible and functional
- [ ] "Analyze Domain" button is present
- [ ] Statistics section loads properly

### **✅ Input Field Responsiveness**
- [ ] **Mobile**: Input field spans full width (no horizontal overflow)
- [ ] **Tablet**: Input field has appropriate max-width
- [ ] **Desktop**: Input field is properly sized
- [ ] Font size is 16px on mobile (prevents zoom)
- [ ] Input accepts text and clears properly

### **✅ Button Responsiveness**
- [ ] **Mobile**: Button spans full width below input
- [ ] **Tablet**: Button positioned next to input
- [ ] **Desktop**: Button properly aligned
- [ ] Button is clickable and responsive

### **✅ Domain Analysis Functionality**
Test with these domains:
- [ ] `cloudgofer.com` (High score - 100)
- [ ] `example.com` (Low score - ~20)
- [ ] `nonexistentdomain123456789.com` (Missing records)

**For each domain, verify:**
- [ ] Analysis completes successfully
- [ ] Security score displays correctly
- [ ] Score breakdown shows all components
- [ ] Color coding works (green for positive, red for zero)

### **✅ Score Breakdown Color Coding**
- [ ] **Zero points** display in **RED** (`#f44336`)
- [ ] **Positive points** display in **GREEN** (`#4CAF50`)
- [ ] **Bonus points** display in **GREEN** (`#4CAF50`)
- [ ] All components show: MX, SPF, DMARC, DKIM

### **✅ Statistics Section**
- [ ] Statistics load without authentication
- [ ] Shows: Total Analyses, Unique Domains, Average Score, Top Provider
- [ ] Responsive layout on all devices
- [ ] No horizontal overflow

### **✅ Mobile-Specific Features**
- [ ] Touch interactions work properly
- [ ] No horizontal scrolling
- [ ] Appropriate padding and margins
- [ ] Text is readable without zooming

## 🔧 **Chrome DevTools Testing**

### **1. Open DevTools**
```
F12 or Right-click → Inspect
```

### **2. Test Different Devices**
```
DevTools → Toggle Device Toolbar (Ctrl+Shift+M)
```

### **3. Test Device Sizes**
- **iPhone 12**: 390x844
- **iPad Pro**: 1024x1366
- **Desktop**: 1920x1080

### **4. Test Responsive Breakpoints**
- **Mobile**: < 768px
- **Tablet**: 769px - 1024px
- **Desktop**: > 1024px

## 🚀 **Automated Testing (Optional)**

### **Prerequisites**
```bash
npm install puppeteer
```

### **Run Tests**
```bash
# Run all tests
node ui_test.js

# Run headless tests (CI/CD)
npm run test:headless

# Run specific device tests
npm run test:mobile
npm run test:desktop
```

## 🐛 **Common Issues & Solutions**

### **Issue: Input Field Overflow on Mobile**
**Solution**: CSS fixes applied
```css
@media (max-width: 768px) {
  .domain-input {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
}
```

### **Issue: Bonus Points Not Green**
**Solution**: Updated CSS
```css
.bonus-indicator {
  color: #4CAF50; /* Green */
}
```

### **Issue: Zero Points Not Red**
**Solution**: Dynamic class application
```javascript
<span className={`component-score ${score === 0 ? 'zero' : ''}`}>
```

## 📊 **Test Results Template**

### **Test Date**: _______________
### **Tester**: _______________

| Device Type | Viewport | Status | Issues |
|-------------|----------|--------|--------|
| Mobile | 390x844 | ✅/❌ | |
| Tablet | 1024x1366 | ✅/❌ | |
| Desktop | 1920x1080 | ✅/❌ | |

### **Key Findings**:
- [ ] All responsive breakpoints working
- [ ] Color coding functioning correctly
- [ ] No horizontal overflow issues
- [ ] Touch interactions working
- [ ] Statistics loading properly

## 🎯 **Performance Testing**

### **Load Times**
- [ ] Initial page load < 3 seconds
- [ ] Domain analysis < 10 seconds
- [ ] Statistics load < 5 seconds

### **Accessibility**
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] High contrast colors
- [ ] Proper focus indicators

## 🔄 **Regression Testing**

After any UI changes, run through:
1. **Mobile testing** (iPhone 12 viewport)
2. **Tablet testing** (iPad Pro viewport)
3. **Desktop testing** (1920x1080 viewport)
4. **Color coding verification**
5. **Input field responsiveness**

## 📝 **Reporting Issues**

When reporting UI issues, include:
- **Device type and viewport size**
- **Browser and version**
- **Screenshot of the issue**
- **Steps to reproduce**
- **Expected vs actual behavior**

---

**Last Updated**: August 7, 2025
**Version**: 1.0.0
