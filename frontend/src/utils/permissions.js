export const permissions = {
  canViewStudents: ['owner', 'professor'],
  canCreateStudent: ['owner', 'professor'],
  canEditStudent: ['owner', 'professor'],
  canDeleteStudent: ['owner'],
  canViewPayments: ['owner', 'professor'],
  canCreatePayment: ['owner', 'professor'],
  canViewReports: ['owner'],
};

export const hasPermission = (user, permission) => {
  return permissions[permission]?.includes(user?.role);
};
